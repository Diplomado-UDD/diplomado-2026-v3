"""Capa de datos: carga del CSV limpio y lectura/escritura de artefactos."""

import json
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT.parent / "data" / "inmuebles_providencia_limpio.csv"
ARTIFACTS = ROOT / "artifacts"

FEATURES = ["dormitorios", "banos", "superficie_m2", "lat", "lon"]
TARGET = "precio_uf"


def load(path: Path = CSV) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Devuelve X, y y el grupo de cada aviso (sus coordenadas).

    Avisos con las mismas coordenadas son el mismo edificio o la misma calle:
    deben quedar en el mismo pliegue para no filtrar información.
    """
    df = pd.read_csv(path).dropna(subset=[TARGET, "superficie_m2", "lat", "lon"])
    groups = df["lat"].round(5).astype(str) + "," + df["lon"].round(5).astype(str)
    return df[FEATURES], df[TARGET], groups


def save(model, cv: pd.DataFrame, test: dict, out: Path = ARTIFACTS) -> None:
    out.mkdir(exist_ok=True)
    joblib.dump(model, out / "modelo.joblib")
    cv.to_csv(out / "cv_resultados.csv", index=False)
    (out / "metricas_test.json").write_text(json.dumps(test, indent=2, ensure_ascii=False))


def load_model(out: Path = ARTIFACTS):
    return joblib.load(out / "modelo.joblib")


def save_conformal(model, meta: dict, out: Path = ARTIFACTS) -> None:
    """Guarda el CatBoost de ajuste y el cuantil q. No pisa el modelo puntual."""
    out.mkdir(exist_ok=True)
    joblib.dump(model, out / "conformal.joblib")
    (out / "conformal.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))


def load_conformal(out: Path = ARTIFACTS):
    model_path = out / "conformal.joblib"
    meta_path = out / "conformal.json"
    if not model_path.exists() or not meta_path.exists():
        raise FileNotFoundError(model_path)
    return joblib.load(model_path), json.loads(meta_path.read_text())
