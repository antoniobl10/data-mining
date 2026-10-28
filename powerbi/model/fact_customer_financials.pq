let
    Source = Csv.Document(File.Contents(GoldFolder & "fact_customer_financials.csv"), [Delimiter=",", Columns=16, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),
    Typed = Table.TransformColumnTypes(Nulls, {{"customer_key", type text}, {"customer_id", type text}, {"country_key", type text}, {"age_group_key", type text}, {"age", type number}, {"balance", type number}, {"estimated_salary", type number}, {"credit_score", type number}, {"tenure", type number}, {"customer_value_score", type number}, {"is_high_value", type logical}, {"is_high_balance", type logical}, {"is_high_income", type logical}, {"is_young_professional", type logical}, {"is_long_term", type logical}, {"is_high_credit", type logical}}, "en-US")
in Typed
