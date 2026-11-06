//! Capa de datos: descarga de páginas, geocodificación y lectura/escritura del CSV.

use reqwest::{StatusCode, Url, blocking::Client};
use serde::{Serialize, de::DeserializeOwned};
use serde_json::Value;
use std::{error::Error, fs, path::Path, time::Duration};

/// Venta, departamentos usados, comuna de Providencia.
const BASE: &str = "https://www.portalinmobiliario.com/venta/departamento/propiedades-usadas/providencia-metropolitana";
const PAGE_SIZE: usize = 48;
const UA: &str =
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/128 Safari/537.36";

pub struct Portal {
    client: Client,
}

impl Portal {
    pub fn new() -> reqwest::Result<Self> {
        let client = Client::builder()
            .user_agent(UA)
            .timeout(Duration::from_secs(30))
            .build()?;
        Ok(Self { client })
    }

    /// HTML de la página `n` (desde 0). `None` al superar el límite de paginación (HTTP 404).
    // ponytail: el portal corta en ~2.016 avisos; partir por rango de precio si se necesitan todos.
    pub fn page(&self, n: usize) -> reqwest::Result<Option<String>> {
        let url = match n {
            0 => BASE.to_string(),
            _ => format!("{BASE}/_Desde_{}", n * PAGE_SIZE + 1),
        };
        let resp = self.client.get(url).send()?;
        if resp.status() == StatusCode::NOT_FOUND {
            return Ok(None);
        }
        resp.error_for_status()?.text().map(Some)
    }
}

/// Geocodificador de OpenStreetMap. Política de uso: máximo 1 consulta por segundo.
pub struct Nominatim {
    client: Client,
}

impl Nominatim {
    const URL: &str = "https://nominatim.openstreetmap.org/search";

    pub fn new() -> reqwest::Result<Self> {
        let client = Client::builder()
            .user_agent("ml-inmuebles-udd/0.1")
            .timeout(Duration::from_secs(30))
            .build()?;
        Ok(Self { client })
    }

    /// Primer resultado de la búsqueda, o `None` si no hay coincidencias.
    pub fn search(&self, q: &str) -> Result<Option<Value>, Box<dyn Error>> {
        let url = Url::parse_with_params(
            Self::URL,
            [
                ("q", q),
                ("format", "jsonv2"),
                ("addressdetails", "1"),
                ("countrycodes", "cl"),
                ("limit", "1"),
            ],
        )?;
        let body = self.client.get(url).send()?.error_for_status()?.text()?;
        let hits: Vec<Value> = serde_json::from_str(&body)?;
        Ok(hits.into_iter().next())
    }
}

pub fn read_csv<T: DeserializeOwned>(path: &Path) -> Result<Vec<T>, Box<dyn Error>> {
    Ok(csv::Reader::from_path(path)?
        .deserialize()
        .collect::<Result<_, _>>()?)
}

pub fn write_csv<T: Serialize>(
    path: &Path,
    rows: impl IntoIterator<Item = T>,
) -> Result<(), Box<dyn Error>> {
    if let Some(dir) = path.parent() {
        fs::create_dir_all(dir)?;
    }
    let mut w = csv::Writer::from_path(path)?;
    for r in rows {
        w.serialize(r)?;
    }
    w.flush()?;
    Ok(())
}
