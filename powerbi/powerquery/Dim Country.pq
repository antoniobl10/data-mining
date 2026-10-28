let
    Source = GoldCsv("dim_country.csv", {"country_key", "country_name", "country_code"}, {{"country_key", Int64.Type}, {"country_name", type text}, {"country_code", type text}}),
    Renamed = Table.RenameColumns(Source, {{"country_key", "Country Key"}, {"country_name", "Country"}, {"country_code", "Country Code"}})
in Renamed
