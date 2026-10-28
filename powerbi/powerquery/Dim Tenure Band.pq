let
    Source = GoldCsv("dim_tenure_band.csv", {"tenure_band_key", "tenure_band", "min_tenure", "max_tenure", "sort_order"}, {{"tenure_band_key", Int64.Type}, {"tenure_band", type text}, {"min_tenure", Int64.Type}, {"max_tenure", Int64.Type}, {"sort_order", Int64.Type}}),
    Renamed = Table.RenameColumns(Source, {{"tenure_band_key", "Tenure Band Key"}, {"tenure_band", "Tenure Band"}, {"min_tenure", "Min Tenure"}, {"max_tenure", "Max Tenure"}, {"sort_order", "Sort Order"}})
in Renamed
