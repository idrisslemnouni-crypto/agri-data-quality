"""Frozen-source quality audit and atomic SQLite warehouse materialization."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from agri_quality.source import download_data, file_hash

KEYS = {
    "yield": ["COUNTY_ID", "FYEAR"],
    "soil": ["COUNTY_ID"],
    "weather": ["COUNTY_ID", "FYEAR", "DEKAD"],
}
FILES = {
    "yield": "YIELD_COUNTY_US.csv",
    "soil": "SOIL_COUNTY_US.csv",
    "weather": "METEO_COUNTY_US.csv",
}
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE county(county_id TEXT PRIMARY KEY, state TEXT NOT NULL);
CREATE TABLE soil(county_id TEXT PRIMARY KEY REFERENCES county(county_id), whc_source REAL NOT NULL CHECK(whc_source>=0), depth_source REAL NOT NULL CHECK(depth_source>=0));
CREATE TABLE yield_observation(county_id TEXT NOT NULL REFERENCES county(county_id), year INTEGER NOT NULL CHECK(year BETWEEN 1900 AND 2100), yield_bu_acre REAL NOT NULL CHECK(yield_bu_acre>=0), PRIMARY KEY(county_id,year));
CREATE TABLE weather(county_id TEXT NOT NULL REFERENCES county(county_id),year INTEGER NOT NULL CHECK(year BETWEEN 1900 AND 2100),dekad INTEGER NOT NULL CHECK(dekad BETWEEN 1 AND 36),tmax_c REAL NOT NULL,tmin_c REAL NOT NULL,tavg_c REAL NOT NULL,prec_mm REAL NOT NULL CHECK(prec_mm>=0),et0_mm REAL NOT NULL CHECK(et0_mm>=0),PRIMARY KEY(county_id,year,dekad),CHECK(tmin_c<=tavg_c AND tavg_c<=tmax_c));
CREATE INDEX weather_year_idx ON weather(year);
CREATE VIEW weather_annual AS SELECT county_id,year,COUNT(*) AS dekads,SUM(prec_mm) AS prec_mm,SUM(et0_mm) AS et0_mm FROM weather GROUP BY county_id,year;
CREATE VIEW yield_coverage AS SELECT y.*,c.state,s.county_id IS NOT NULL AS has_soil,COALESCE(w.dekads,0) AS weather_dekads FROM yield_observation y JOIN county c USING(county_id) LEFT JOIN soil s USING(county_id) LEFT JOIN weather_annual w USING(county_id,year);
"""


def validate(frame, kind):
    keys = KEYS[kind]
    reason = pd.Series("", index=frame.index, dtype="str")

    def flag(mask, label):
        reason.loc[mask] = reason.loc[mask] + label + ";"

    ids = frame.COUNTY_ID.astype("string")
    flag(ids.isna() | ~ids.str.match(r"^[A-Z]{2}_.+").fillna(False), "invalid_county_key")
    numeric = [c for c in frame.columns if c != "COUNTY_ID"]
    values = frame[numeric].apply(pd.to_numeric, errors="coerce")
    flag(~np.isfinite(values).all(axis=1), "nonfinite_numeric")
    for key in [k for k in keys if k != "COUNTY_ID"]:
        flag(values[key].ne(values[key].round()), "noninteger_key")
    if "FYEAR" in values:
        flag(~values.FYEAR.between(1900, 2100), "invalid_year")
    flag(frame.duplicated(keys, keep=False), "duplicate_key")
    if kind == "yield":
        flag(values.YIELD < 0, "negative_yield")
    if kind == "soil":
        flag((values[["SM_WHC", "SM_DEPTH"]] < 0).any(axis=1), "negative_soil_amount")
    if kind == "weather":
        flag(~values.DEKAD.between(1, 36), "invalid_dekad")
        flag(
            (values[["PREC", "ET0", "WSPD", "RAD", "VPRES"]] < 0).any(axis=1),
            "negative_weather_amount",
        )
        flag((values.TMIN > values.TAVG) | (values.TAVG > values.TMAX), "inconsistent_temperature")
    clean = frame.loc[reason.eq("")].copy()
    clean[numeric] = values.loc[clean.index]
    rejected = frame.loc[reason.ne("")].copy()
    rejected["source_row"] = rejected.index + 2
    rejected["reason"] = reason.loc[rejected.index]
    rejected["table"] = kind
    return clean, rejected


def load_warehouse(path, frames):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".part")
    # Own temporary file inside the warehouse directory only.
    if temporary.exists():
        temporary.unlink()
    counties = sorted(set().union(*(set(f.COUNTY_ID) for f in frames.values())))
    with closing(sqlite3.connect(temporary)) as db:
        db.executescript(SCHEMA)
        with db:
            db.executemany("INSERT INTO county VALUES (?,?)", [(c, c[:2]) for c in counties])
            db.executemany(
                "INSERT INTO soil VALUES (?,?,?)",
                frames["soil"][["COUNTY_ID", "SM_WHC", "SM_DEPTH"]].itertuples(
                    index=False, name=None
                ),
            )
            db.executemany(
                "INSERT INTO yield_observation VALUES (?,?,?)",
                frames["yield"][["COUNTY_ID", "FYEAR", "YIELD"]].itertuples(index=False, name=None),
            )
            columns = ["COUNTY_ID", "FYEAR", "DEKAD", "TMAX", "TMIN", "TAVG", "PREC", "ET0"]
            db.executemany(
                "INSERT INTO weather VALUES (?,?,?,?,?,?,?,?)",
                frames["weather"][columns].itertuples(index=False, name=None),
            )
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    temporary.replace(path)


def run(root):
    raw = download_data(root / "data/raw")
    clean, rejected, audit = {}, {}, {}
    for kind, file in FILES.items():
        source = pd.read_csv(raw / file)
        clean[kind], rejected[kind] = validate(source, kind)
        audit[kind] = {
            "source_rows": len(source),
            "loaded_rows": len(clean[kind]),
            "quarantined_rows": len(rejected[kind]),
            "sha256": file_hash(raw / file),
            "missing_cells": int(source.isna().sum().sum()),
            "duplicate_key_rows": int(source.duplicated(KEYS[kind], keep=False).sum()),
        }
    warehouse = root / "data/processed/agriculture.sqlite"
    load_warehouse(warehouse, clean)
    reports = root / "reports"
    (reports / "figures").mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(warehouse)) as db:
        coverage = pd.read_sql_query(
            "SELECT state,year,COUNT(*) AS yield_rows,SUM(has_soil) AS soil_matches,SUM(weather_dekads=36) AS complete_weather_matches,AVG(yield_bu_acre) AS unweighted_yield_bu_acre FROM yield_coverage GROUP BY state,year ORDER BY state,year",
            db,
        )
        summary = dict(
            zip(
                ["yield_rows", "missing_soil_rows", "incomplete_weather_rows", "zero_yield_rows"],
                db.execute(
                    "SELECT COUNT(*),SUM(NOT has_soil),SUM(weather_dekads!=36),SUM(yield_bu_acre=0) FROM yield_coverage"
                ).fetchone(),
                strict=True,
            )
        )
    coverage.to_csv(reports / "coverage.csv", index=False)
    quarantine = pd.concat(rejected.values(), ignore_index=True)
    quarantine.head(20).to_csv(reports / "quarantine-examples.csv", index=False)
    pd.Series({k: int(v) for k, v in quarantine.reason.value_counts().items()}).to_csv(
        reports / "quarantine-reasons.csv", header=["rows"]
    )
    evidence = {
        "source_audit": audit,
        "coverage": summary,
        "scope": "Complete archived county tables; missing joins are coverage warnings; soil units unverified",
    }
    (reports / "quality-report.json").write_text(json.dumps(evidence, indent=2, allow_nan=False))
    heat = coverage.assign(fraction=lambda x: x.complete_weather_matches / x.yield_rows).pivot(
        index="state", columns="year", values="fraction"
    )
    fig, ax = plt.subplots(figsize=(12, 7))
    chart = ax.imshow(heat, aspect="auto", vmin=0, vmax=1, cmap="YlGn")
    ax.set(
        yticks=range(len(heat)),
        yticklabels=heat.index,
        xticks=range(len(heat.columns)),
        xticklabels=heat.columns,
        title="Fraction of yield rows with all 36 weather dekads\nMissing coverage is retained, not imputed",
    )
    ax.tick_params(axis="x", rotation=90)
    fig.colorbar(chart, ax=ax, label="Complete weather coverage fraction")
    fig.tight_layout()
    fig.savefig(reports / "figures/coverage.png", dpi=150)
    plt.close(fig)
    return evidence


if __name__ == "__main__":
    print(json.dumps(run(Path.cwd()), indent=2))
