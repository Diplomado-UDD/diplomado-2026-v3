"""Presentación: CLI.

modelo train [--n-iter N] [--models a b ...]  compara modelos, ajusta el ganador y lo guarda.
modelo conformal [--alpha A]                  ajusta CatBoost y calibra el intervalo.
modelo predict DORM BANOS M2 LAT LON          predice el precio en UF.
"""

import argparse

from . import conformal, data, evaluate
from .models import CATALOG


def train(args) -> None:
    X, y, g = data.load()
    Xtr, Xte, ytr, yte, gtr = evaluate.split(X, y, g, seed=args.seed)
    print(f"train {len(Xtr)} / test {len(Xte)} avisos, {g.nunique()} grupos")

    cv = evaluate.nested_cv(Xtr, ytr, gtr, args.models, args.n_iter, seed=args.seed)
    res = evaluate.summary(cv)
    print(res.round(3).to_string())

    best = res.index[0]
    model = evaluate.fit_final(best, Xtr, ytr, gtr, args.n_iter, seed=args.seed)
    test = {"modelo": best} | evaluate.metrics(yte, model.predict(Xte))
    data.save(model, cv, test)
    print(f"test: {test}")
    print(f"artefactos en {data.ARTIFACTS}")


def intervalo(args) -> None:
    X, y, g = data.load()
    Xtr, Xte, ytr, yte, gtr = evaluate.split(X, y, g, seed=args.seed)
    Xfit, Xcal, yfit, ycal, gfit = conformal.split_calibration(
        Xtr, ytr, gtr, cal_size=args.cal_size, seed=args.seed
    )
    print(f"ajuste {len(Xfit)} / calibración {len(Xcal)} / test {len(Xte)}")

    model = evaluate.fit_final("catboost", Xfit, yfit, gfit, args.n_iter, seed=args.seed)
    q = conformal.calibrate(model, Xcal, ycal, alpha=args.alpha)
    pred = model.predict(Xte)
    cov = conformal.coverage(yte, pred, q)
    punto = evaluate.metrics(yte, pred)
    bands = conformal.coverage_by_band(yte, pred, q)
    meta = {
        "modelo": "catboost",
        "alpha": args.alpha,
        "q": q,
        "margen": conformal.margin(q),
        "n_fit": len(Xfit),
        "n_cal": len(Xcal),
        "n_test": cov["n"],
        "cobertura": cov["cobertura"],
        "ancho_medio_uf": cov["ancho_medio_uf"],
        **{f"test_{k}": v for k, v in punto.items()},
        "tramos": [
            {
                "tramo": str(row.tramo),
                "n": int(row.n),
                "cobertura": float(row.cobertura),
                "ancho_medio_uf": float(row.ancho_medio_uf),
            }
            for row in bands.itertuples(index=False)
        ],
    }
    data.save_conformal(model, meta)
    print(f"q={q:.3f}  margen ±{meta['margen']:.1%}")
    print("test:", {k: round(v, 3) for k, v in punto.items()})
    print("cobertura:", {k: round(v, 3) if isinstance(v, float) else v for k, v in cov.items()})
    print(bands.round(3).to_string(index=False))
    print(f"artefactos en {data.ARTIFACTS}")


def predict(args) -> None:
    try:
        model, meta = data.load_conformal()
    except FileNotFoundError:
        uf = evaluate.predict_one(
            data.load_model(), args.dorm, args.banos, args.m2, args.lat, args.lon
        )
        print(f"{uf:,.0f} UF")
        return
    punto, lo, hi = conformal.predict_interval(
        model, meta["q"], args.dorm, args.banos, args.m2, args.lat, args.lon
    )
    print(f"{punto:,.0f} UF [{lo:,.0f}, {hi:,.0f}]")


def main() -> None:
    p = argparse.ArgumentParser(prog="modelo")
    sub = p.add_subparsers(required=True)

    t = sub.add_parser("train")
    t.add_argument("--n-iter", type=int, default=20)
    t.add_argument("--models", nargs="+", choices=list(CATALOG))
    t.add_argument("--seed", type=int, default=42)
    t.set_defaults(func=train)

    c = sub.add_parser("conformal")
    c.add_argument("--alpha", type=float, default=0.1)
    c.add_argument("--cal-size", type=float, default=0.2)
    c.add_argument("--n-iter", type=int, default=20)
    c.add_argument("--seed", type=int, default=42)
    c.set_defaults(func=intervalo)

    q = sub.add_parser("predict")
    for a in ("dorm", "banos", "m2", "lat", "lon"):
        q.add_argument(a, type=float)
    q.set_defaults(func=predict)

    args = p.parse_args()
    args.func(args)
