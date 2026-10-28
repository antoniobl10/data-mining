let
    Source = Csv.Document(File.Contents(GoldFolder & "dim_customer.csv"), [Delimiter=",", Columns=17, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(Nulls, {{"customer_key", type text}, {"customer_id", type text}, {"country", type text}, {"gender", type text}, {"age", type number}, {"age_group", type text}, {"tenure", type number}, {"tenure_band", type text}, {"credit_score", type number}, {"credit_score_band", type text}, {"balance", type number}, {"balance_band", type text}, {"estimated_salary", type number}, {"salary_band", type text}, {"customer_value_segment", type text}, {"primary_segment", type text}, {"data_quality_flag", type text}}, "en-US")
in Typed
