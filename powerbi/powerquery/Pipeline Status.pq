let
    Manifest = Json.Document(File.Contents(GoldBuildPath & "/manifest.json")),
    Upstream = Manifest[upstream_silver_manifest],
    Result = #table(type table [Source Rows=Int64.Type, Silver Rows=Int64.Type, Quarantine Rows=Int64.Type, Silver Checks Failed=Int64.Type, Gold Build=text, Source Batch=text, Build Timestamp=text],
        {{Upstream[bronze_rows], Upstream[silver_rows], Upstream[quarantine_rows], Record.FieldOrDefault(Upstream[quality_statuses], "FAIL", 0), Manifest[gold_build_id], Manifest[source_batch_id], Manifest[gold_build_timestamp]}})
in Result
