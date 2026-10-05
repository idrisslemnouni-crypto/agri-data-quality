import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from agri_quality.pipeline import load_warehouse, validate


def fixtures():
    # Deliberately artificial unit-test rows, never used in reports.
    return {
        "yield": pd.DataFrame([["IA_TEST", 2020, 0.0]], columns=["COUNTY_ID", "FYEAR", "YIELD"]),
        "soil": pd.DataFrame(
            [["IA_TEST", 13.0, 100.0]], columns=["COUNTY_ID", "SM_WHC", "SM_DEPTH"]
        ),
        "weather": pd.DataFrame(
            [["IA_TEST", 2020, 1, 20.0, 10.0, 15.0, 2.0, 3.0]],
            columns=["COUNTY_ID", "FYEAR", "DEKAD", "TMAX", "TMIN", "TAVG", "PREC", "ET0"],
        ),
    }


def test_zero_yield_retained_and_duplicates_quarantined():
    f = fixtures()["yield"]
    assert len(validate(f, "yield")[0]) == 1
    good, bad = validate(pd.concat([f, f], ignore_index=True), "yield")
    assert len(good) == 0 and len(bad) == 2
    assert bad.reason.str.contains("duplicate_key").all()


def test_nonfinite_and_negative_rows_quarantined():
    f = fixtures()["yield"]
    f.loc[0, "YIELD"] = float("inf")
    assert "nonfinite_numeric" in validate(f, "yield")[1].reason.iloc[0]
    f.loc[0, "YIELD"] = -1
    assert "negative_yield" in validate(f, "yield")[1].reason.iloc[0]


def test_idempotent_rebuild_and_foreign_key_contract(tmp_path):
    path = tmp_path / "warehouse.sqlite"
    for _ in range(2):
        load_warehouse(path, fixtures())
        with closing(sqlite3.connect(path)) as db:
            db.execute("PRAGMA foreign_keys=ON")
            assert db.execute("SELECT COUNT(*) FROM yield_coverage").fetchone()[0] == 1
            assert not db.execute("PRAGMA foreign_key_check").fetchall()
            with pytest.raises(sqlite3.IntegrityError):
                db.execute("INSERT INTO yield_observation VALUES ('IA_UNKNOWN',2020,2)")


def test_failed_rebuild_preserves_previous_database(tmp_path):
    path = tmp_path / "warehouse.sqlite"
    load_warehouse(path, fixtures())
    before = path.read_bytes()
    f = fixtures()
    f["yield"].loc[0, "YIELD"] = -1
    with pytest.raises(sqlite3.IntegrityError):
        load_warehouse(path, f)
    assert path.read_bytes() == before
