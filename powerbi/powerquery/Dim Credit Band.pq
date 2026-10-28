let
    Source = GoldCsv("dim_credit_band.csv", {"credit_band_key", "credit_score_band", "min_score", "max_score", "sort_order", "credit_quality_level"}, {{"credit_band_key", Int64.Type}, {"credit_score_band", type text}, {"min_score", Int64.Type}, {"max_score", Int64.Type}, {"sort_order", Int64.Type}, {"credit_quality_level", Int64.Type}}),
    Renamed = Table.RenameColumns(Source, {{"credit_band_key", "Credit Band Key"}, {"credit_score_band", "Credit Band"}, {"min_score", "Min Score"}, {"max_score", "Max Score"}, {"sort_order", "Sort Order"}, {"credit_quality_level", "Credit Quality Level"}})
in Renamed
