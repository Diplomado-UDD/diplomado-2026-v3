//! Lógica de negocio: extracción, filtros y normalización de avisos.

use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;

const COMUNA: &str = "Providencia";

#[derive(Debug, Serialize, Deserialize)]
pub struct Inmueble {
    pub id: String,
    pub titulo: String,
    pub precio: Option<f64>,
    pub moneda: String,
    pub dormitorios: Option<f64>,
    pub banos: Option<f64>,
    pub superficie_texto: String,
    pub superficie_m2: Option<f64>,
    pub direccion: String,
    pub url: String,
    #[serde(default)]
    pub lat: Option<f64>,
    #[serde(default)]
    pub lon: Option<f64>,
    #[serde(default)]
    pub barrio: Option<String>,
    /// Precisión de la geocodificación según OSM: building, road, neighbourhood...
    #[serde(default)]
    pub geo_nivel: Option<String>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Geo {
    pub lat: f64,
    pub lon: f64,
    pub barrio: Option<String>,
    pub nivel: Option<String>,
}

impl Inmueble {
    pub fn has_coords(&self) -> bool {
        self.lat.is_some() && self.lon.is_some()
    }

    pub fn set_geo(&mut self, g: Option<&Geo>) {
        self.lat = g.map(|g| g.lat);
        self.lon = g.map(|g| g.lon);
        self.barrio = g.and_then(|g| g.barrio.clone());
        self.geo_nivel = g.and_then(|g| g.nivel.clone());
    }
}

/// Consultas a Nominatim, de la más específica a la más general.
/// Una dirección que solo indica la comuna no se geocodifica (daría el centro de la comuna).
pub fn geo_queries(direccion: &str) -> Vec<String> {
    let first = direccion.split(',').next().unwrap_or_default().trim();
    if first.is_empty() || first.eq_ignore_ascii_case(COMUNA) {
        return vec![];
    }
    let mut q = vec![format!("{direccion}, Chile")];
    let fallback = format!("{first}, {COMUNA}, Chile");
    if fallback != q[0] {
        q.push(fallback);
    }
    q
}

/// Resultado de Nominatim, o `None` si cae fuera de la comuna.
pub fn to_geo(hit: &Value) -> Option<Geo> {
    let addr = &hit["address"];
    if addr["city"].as_str() != Some(COMUNA) {
        return None;
    }
    let text = |v: &Value| v.as_str().map(String::from);
    Some(Geo {
        lat: hit["lat"].as_str()?.parse().ok()?,
        lon: hit["lon"].as_str()?.parse().ok()?,
        barrio: text(&addr["neighbourhood"]).or_else(|| text(&addr["quarter"])),
        nivel: text(&hit["addresstype"]),
    })
}

/// Objetos `polycard` embebidos en el HTML del listado (cada aviso aparece repetido).
pub fn extract_cards(html: &str) -> Vec<Value> {
    const KEY: &str = "\"polycard\":";
    html.match_indices(KEY)
        .filter_map(|(i, _)| {
            serde_json::Deserializer::from_str(&html[i + KEY.len()..])
                .into_iter::<Value>()
                .next()?
                .ok()
        })
        .collect()
}

/// Promedio de los números del texto: "38 - 63 m² útiles" -> 50.5, "92 m²" -> 92.
/// Formato chileno: "." separa miles y "," separa decimales.
pub fn mean(text: &str) -> Option<f64> {
    let nums: Vec<f64> = text
        .split(|c: char| !(c.is_ascii_digit() || c == '.' || c == ','))
        .filter_map(|t| t.replace('.', "").replace(',', ".").parse().ok())
        .collect();
    (!nums.is_empty()).then(|| nums.iter().sum::<f64>() / nums.len() as f64)
}

/// Aviso normalizado, o `None` si es proyecto nuevo o está fuera de la comuna.
pub fn to_inmueble(card: &Value) -> Option<Inmueble> {
    let meta = &card["metadata"];
    // DEVELOPMENT_* = proyecto inmobiliario (nuevo); INDIVIDUAL_* = usado.
    if !meta["domain_id"].as_str()?.contains("INDIVIDUAL") {
        return None;
    }
    let comps: HashMap<&str, &Value> = card["components"]
        .as_array()?
        .iter()
        .filter_map(|c| Some((c["id"].as_str()?, &c[c["type"].as_str()?])))
        .collect();

    let direccion = comps.get("location")?["text"].as_str()?.trim();
    let comuna = direccion.rsplit(',').next()?.trim();
    if !comuna.eq_ignore_ascii_case(COMUNA) {
        return None;
    }

    let attrs: Vec<&str> = comps
        .get("attributes_list")
        .and_then(|a| a["texts"].as_array())
        .map(|t| t.iter().filter_map(Value::as_str).collect())
        .unwrap_or_default();
    let attr = |k: &str| attrs.iter().find(|t| t.contains(k)).copied();
    let superficie = attr("m²").unwrap_or_default();
    let price = &comps.get("price")?["current_price"];
    let id = meta["id"].as_str()?;

    Some(Inmueble {
        id: id.into(),
        titulo: comps.get("title")?["text"].as_str()?.into(),
        precio: price["value"].as_f64(),
        moneda: price["currency"].as_str().unwrap_or_default().into(),
        dormitorios: attr("dormitorio").and_then(mean),
        banos: attr("baño").and_then(mean),
        superficie_texto: superficie.into(),
        superficie_m2: mean(superficie),
        direccion: direccion.into(),
        // metadata.url de los avisos pagados es un enlace de seguimiento; se arma la canónica.
        lat: None,
        lon: None,
        barrio: None,
        geo_nivel: None,
        url: format!(
            "https://www.portalinmobiliario.com/MLC-{}-_JM",
            id.trim_start_matches("MLC")
        ),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn card(domain: &str, location: &str) -> Value {
        json!({
            "metadata": {"id": "MLC123", "domain_id": domain},
            "components": [
                {"type": "title", "id": "title", "title": {"text": "Depto"}},
                {"type": "price", "id": "price", "price": {"current_price": {"value": 6990, "currency": "CLF"}}},
                {"type": "attributes_list", "id": "attributes_list",
                 "attributes_list": {"texts": ["1 a 2 dormitorios", "2 baños", "32 - 45 m² útiles"]}},
                {"type": "location", "id": "location", "location": {"text": location}}
            ]
        })
    }

    #[test]
    fn mean_normaliza_rangos_y_formato_chileno() {
        assert_eq!(mean("32 - 45 m² útiles"), Some(38.5));
        assert_eq!(mean("92 m² útiles"), Some(92.0));
        assert_eq!(mean("1.200 m² útiles"), Some(1200.0));
        assert_eq!(mean("45,5 m² útiles"), Some(45.5));
        assert_eq!(mean("sin datos"), None);
    }

    #[test]
    fn filtra_usados_de_providencia() {
        let i = to_inmueble(&card(
            "MLC-INDIVIDUAL_APARTMENTS_FOR_SALE",
            "Suecia 1800, Campus Oriente, Providencia",
        ))
        .unwrap();
        assert_eq!(
            (i.superficie_m2, i.dormitorios, i.banos),
            (Some(38.5), Some(1.5), Some(2.0))
        );
        assert_eq!(i.url, "https://www.portalinmobiliario.com/MLC-123-_JM");
        assert!(
            to_inmueble(&card(
                "MLC-DEVELOPMENT_APARTMENTS_FOR_SALE",
                "Bilbao 514, Providencia"
            ))
            .is_none()
        );
        assert!(
            to_inmueble(&card(
                "MLC-INDIVIDUAL_APARTMENTS_FOR_SALE",
                "Apoquindo 3000, Las Condes"
            ))
            .is_none()
        );
    }

    #[test]
    fn geo_queries_y_validacion_de_comuna() {
        assert_eq!(
            geo_queries("Holanda, 1513, Las Lilas, Providencia"),
            [
                "Holanda, 1513, Las Lilas, Providencia, Chile",
                "Holanda, Providencia, Chile"
            ]
        );
        assert_eq!(
            geo_queries("Las Lilas, Providencia"),
            ["Las Lilas, Providencia, Chile"]
        );
        assert!(geo_queries("Providencia").is_empty());

        let hit = |city: &str| {
            json!({"lat": "-33.43", "lon": "-70.60", "addresstype": "building",
                   "address": {"city": city, "neighbourhood": "Barrio Plaza de la Alcaldesa"}})
        };
        let g = to_geo(&hit("Providencia")).unwrap();
        assert_eq!((g.lat, g.lon), (-33.43, -70.60));
        assert_eq!(g.barrio.as_deref(), Some("Barrio Plaza de la Alcaldesa"));
        assert!(to_geo(&hit("Ñuñoa")).is_none());
    }
}
