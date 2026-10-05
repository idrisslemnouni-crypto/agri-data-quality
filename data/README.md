# Source and units

Paudel, Dilli; de Wit, Allard; Boogaard, Hendrik (2023). Sample data for A weakly supervised framework for high resolution crop yield forecasts, v1.0. [Zenodo DOI](https://doi.org/10.5281/zenodo.7751191), CC BY 4.0. Code is MIT; this source and derived aggregates retain attribution under CC BY 4.0. No original collection is claimed.

Three fixed CSV entries from county-data.zip; official size 50,051,357 bytes and MD5 b7cf000262da294caffc2fea39932246 are verified. Annual maize yield is bushels/acre; temperatures °C, precipitation/ET0 mm per calendar dekad. Soil water holding capacity and depth retain source numeric units **unverified**. VPRES, WSPD and RAD are audited as distributed but excluded from the warehouse until units are confirmed. A dekad spans ten days or the month's remainder, not a daily observation.

This project audits the whole source rather than the eight-state ML subset. Missing soil/weather joins are coverage warnings, not evidence that a yield observation is incorrect. Zero yields are retained and flagged for semantic review. Raw source files and the generated database are saved locally and ignored in Git.
