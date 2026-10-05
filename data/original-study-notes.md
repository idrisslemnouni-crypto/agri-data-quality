# Data provenance and usage

Source: Paudel, Dilli; de Wit, Allard; Boogaard, Hendrik. *Sample data for A weakly supervised framework for high resolution crop yield forecasts*, version 1.0. [Zenodo record](https://zenodo.org/records/7751191), [DOI](https://doi.org/10.5281/zenodo.7751191). Dataset metadata declares **CC BY 4.0**; this is separate from the MIT code license. Attribution and these provenance links must accompany derived data. No original collection or contribution to this dataset is claimed.

Download: `https://zenodo.org/records/7751191/files/county-data.zip?download=1`. Exact archive size: 50,051,357 bytes. Official MD5: `b7cf000262da294caffc2fea39932246`. The downloader verifies both before extracting only three fixed archive entries; raw files remain ignored by Git. SHA-256 hashes of extracted files are recorded in `reports/metrics.json`.

| File | Source rows, observed | Variables used | Original provenance / units |
|---|---:|---|---|
| YIELD_COUNTY_US.csv | 45,499 | COUNTY_ID, FYEAR, YIELD | USDA/NASS annual maize yields, bushels/acre |
| METEO_COUNTY_US.csv | 577,980 | COUNTY_ID, FYEAR, DEKAD, TAVG, TMAX, TMIN, PREC, ET0 | Copernicus agrometeorological reanalysis indicators; °C and mm/dekad |
| SOIL_COUNTY_US.csv | 917 | COUNTY_ID, SM_WHC | WISE soil water holding capacity as distributed by the authors |

The source yield history spans 1994–2018; weather starts in 2000. This study restricts itself to eight states in 2000–2018. `SM_DEPTH` is supplied by the archive but is excluded from modeling. The Zenodo landing page describes capacity without a precise SM_WHC unit; we preserve its original numeric scale, do **not** relabel it as mm, and make no quantitative irrigation recommendation from it.

Weather uses calendar dekads: 1–10, 11–20 and the remainder of each month. April–July corresponds to 10–21. Monthly temperature averages weight the three dekads by calendar duration; maxima/minima take extrema; precipitation and ET0 sum; balance = precipitation − ET0. No daily growing-degree-day or count-of-hot-days feature is inferred from aggregated temperatures.

Joins: county-year for yields/weather; county for soil. Missing soil/weather rows are excluded and counted. In the executed table 2,541 selected labels have no soil match; 9,524 rows across 528 counties remain. The archive contains 501 zero yields, six in the selected states/period, but none survive the soil join. Zero yields are not arbitrarily discarded; their semantics would require investigation if retained. Reporting is unweighted by harvested area; the observations are counties, not individual farms.

Excluded modalities: smoothed FAPAR (possible future-window availability), crop model outputs TAGP/TWSO/DVS, harvested areas and grid-level modeled yield labels. The dataset was prepared by other researchers; this repository implements a separate tabular benchmark, not their published weak-supervision model.

`reports/test_predictions.csv` and `reports/example-input.json` contain transformed public source values plus generated predictions; attribute the source under CC BY 4.0 when redistributing. No raw dataset or local model is committed. Download using `python -m crop_yield.cli download`.
