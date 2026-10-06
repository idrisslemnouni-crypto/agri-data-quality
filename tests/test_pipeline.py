import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from agri_quality.pipeline import FILES, load_warehouse, run, validate


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


@pytest.mark.parametrize("kind", ["yield", "weather"])
def test_numeric_key_representations_are_one_duplicate_group(kind):
    frame = fixtures()[kind]
    frame = pd.concat([frame] * 4, ignore_index=True)
    frame["FYEAR"] = [2020, "2020", "2020.0", "2021"]
    if kind == "weather":
        frame["DEKAD"] = [1, "1", "1.0", "1"]
        for name in ["WSPD", "RAD", "VPRES"]:
            frame[name] = 1.0
    original = frame.copy(deep=True)
    clean, rejected = validate(frame, kind)
    assert clean.FYEAR.tolist() == [2021]
    assert rejected.source_row.tolist() == [2, 3, 4]
    assert rejected.reason.str.contains("duplicate_key;").all()
    pd.testing.assert_frame_equal(rejected[original.columns], original.iloc[:3])
    pd.testing.assert_frame_equal(frame, original)


def test_pipeline_duplicate_audit_matches_canonical_quarantine(tmp_path, monkeypatch):
    frames = fixtures()
    frames["yield"] = pd.concat([frames["yield"]] * 4, ignore_index=True)
    frames["yield"]["FYEAR"] = ["2020", "2020.0", "2021", "invalid"]
    for name in ["WSPD", "RAD", "VPRES"]:
        frames["weather"][name] = 1.0
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    for kind, filename in FILES.items():
        frames[kind].to_csv(raw / filename, index=False)
    monkeypatch.setattr("agri_quality.pipeline.download_data", lambda _: raw)
    audit = run(tmp_path)["source_audit"]["yield"]
    assert audit["duplicate_key_rows"] == 2
    assert audit["loaded_rows"] == 1 and audit["quarantined_rows"] == 3
    with closing(sqlite3.connect(tmp_path / "data/processed/agriculture.sqlite")) as db:
        assert db.execute("SELECT year FROM yield_observation").fetchall() == [(2021,)]


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
