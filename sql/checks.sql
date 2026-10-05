-- All joins use an annual weather aggregate: avoid multiplying annual yields.
SELECT COUNT(*) AS missing_soil FROM yield_coverage WHERE has_soil=0;
SELECT year,COUNT(*) AS incomplete_weather FROM yield_coverage WHERE weather_dekads!=36 GROUP BY year;
SELECT state,year,COUNT(*) AS counties,AVG(yield_bu_acre) AS unweighted_mean_bu_acre FROM yield_coverage GROUP BY state,year;
PRAGMA foreign_key_check;
PRAGMA integrity_check;
