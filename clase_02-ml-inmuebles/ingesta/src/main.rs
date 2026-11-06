//! Presentación: CLI.
//!   scrape [csv]  extrae: recorre el listado y escribe el CSV.
//!   geo [csv]     transforma: agrega lat, lon, barrio y geo_nivel al CSV (reanudable).
//!   filter [csv]  carga: escribe <csv>_geo.csv solo con avisos que tienen coordenadas.
//!   etl [csv]     ejecuta scrape, geo y filter en secuencia.

mod parse;
mod source;

use std::{
    collections::{BTreeMap, HashMap},
    error::Error,
    path::{Path, PathBuf},
    thread,
    time::Duration,
};

const DEFAULT_OUT: &str = concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/../data/inmuebles_providencia.csv"
);

fn main() -> Result<(), Box<dyn Error>> {
    let mut args = std::env::args().skip(1);
    let cmd = args.next().unwrap_or_else(|| "scrape".into());
    let path = PathBuf::from(args.next().unwrap_or_else(|| DEFAULT_OUT.into()));
    match cmd.as_str() {
        "scrape" => scrape(&path),
        "geo" => geo(&path),
        "filter" => filter(&path),
        "etl" => scrape(&path)
            .and_then(|_| geo(&path))
            .and_then(|_| filter(&path)),
        _ => Err(format!("comando desconocido: {cmd} (use scrape | geo | filter | etl)").into()),
    }
}

fn filter(path: &Path) -> Result<(), Box<dyn Error>> {
    let rows: Vec<parse::Inmueble> = source::read_csv(path)?;
    let total = rows.len();
    let geo: Vec<_> = rows
        .into_iter()
        .filter(parse::Inmueble::has_coords)
        .collect();
    let out = path.with_file_name(format!(
        "{}_geo.csv",
        path.file_stem().unwrap_or_default().to_string_lossy()
    ));
    source::write_csv(&out, &geo)?;
    eprintln!(
        "{}/{total} avisos con coordenadas en {}",
        geo.len(),
        out.display()
    );
    Ok(())
}

fn scrape(out: &Path) -> Result<(), Box<dyn Error>> {
    let portal = source::Portal::new()?;
    let mut rows = BTreeMap::new();

    for n in 0.. {
        let Some(html) = portal.page(n)? else { break };
        let cards = parse::extract_cards(&html);
        if cards.is_empty() {
            break;
        }
        for i in cards.iter().filter_map(parse::to_inmueble) {
            rows.entry(i.id.clone()).or_insert(i);
        }
        eprintln!("página {}: {} avisos acumulados", n + 1, rows.len());
        thread::sleep(Duration::from_secs(1));
    }

    source::write_csv(out, rows.values())?;
    eprintln!("{} avisos en {}", rows.len(), out.display());
    Ok(())
}

fn geo(path: &Path) -> Result<(), Box<dyn Error>> {
    let mut rows: Vec<parse::Inmueble> = source::read_csv(path)?;
    let nominatim = source::Nominatim::new()?;
    let mut cache: HashMap<String, Option<parse::Geo>> = HashMap::new();

    for r in rows.iter_mut().filter(|r| r.lat.is_none()) {
        if !cache.contains_key(&r.direccion) {
            let mut geo = None;
            for q in parse::geo_queries(&r.direccion) {
                thread::sleep(Duration::from_secs(1));
                match nominatim.search(&q) {
                    Ok(hit) => geo = hit.as_ref().and_then(parse::to_geo),
                    Err(e) => eprintln!("error en {q:?}: {e}"),
                }
                if geo.is_some() {
                    break;
                }
            }
            cache.insert(r.direccion.clone(), geo);
            if cache.len().is_multiple_of(50) {
                eprintln!("{} direcciones consultadas", cache.len());
            }
        }
        r.set_geo(cache[&r.direccion].as_ref());
    }

    source::write_csv(path, &rows)?;
    let ok = rows.iter().filter(|r| r.lat.is_some()).count();
    eprintln!(
        "{ok}/{} avisos geocodificados en {}",
        rows.len(),
        path.display()
    );
    Ok(())
}
