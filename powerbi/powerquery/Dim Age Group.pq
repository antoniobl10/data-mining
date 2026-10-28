let
    Source = GoldCsv("dim_age_group.csv", {"age_group_key", "age_group", "min_age", "max_age", "sort_order"}, {{"age_group_key", Int64.Type}, {"age_group", type text}, {"min_age", Int64.Type}, {"max_age", Int64.Type}, {"sort_order", Int64.Type}}),
    Renamed = Table.RenameColumns(Source, {{"age_group_key", "Age Group Key"}, {"age_group", "Age Group"}, {"min_age", "Min Age"}, {"max_age", "Max Age"}, {"sort_order", "Sort Order"}})
in Renamed
