let
    Source = Csv.Document(File.Contents(GoldFolder & "dim_age_group.csv"), [Delimiter=",", Columns=3, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(Nulls, {{"age_group_key", type text}, {"age_group", type text}, {"sort_order", Int64.Type}}, "en-US")
in Typed
