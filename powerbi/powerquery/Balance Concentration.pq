let
    Source = GoldCsv("mart_balance_concentration.csv", {"cohort", "requested_fraction", "balance_share"}, {{"cohort", type text}, {"requested_fraction", type number}, {"balance_share", type number}}),
    Renamed = Table.RenameColumns(Source, {{"cohort", "Cohort"}, {"requested_fraction", "Requested Fraction"}, {"balance_share", "Snapshot Balance Share"}})
in Renamed
