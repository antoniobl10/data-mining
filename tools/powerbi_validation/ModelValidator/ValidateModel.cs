using Microsoft.AnalysisServices.Tabular;

if (args.Length == 4 && args[0] == "--live-sync-analytics")
{
    using var server = new Server();
    server.Connect("Data Source=localhost:" + args[1]);
    if (server.Databases.Count != 1) throw new InvalidOperationException("Expected one Desktop database");
    var authored = Microsoft.AnalysisServices.Tabular.JsonSerializer.DeserializeDatabase(File.ReadAllText(args[2]));
    using var manifest = System.Text.Json.JsonDocument.Parse(File.ReadAllText(args[3]));
    if (manifest.RootElement.GetProperty("data_origin").GetString() != "SYNTHETIC DEMO ANALYTICS") throw new InvalidOperationException("Expected validated synthetic analytics");
    var folder=manifest.RootElement.GetProperty("powerbi_path").GetString()!;
    var model=server.Databases[0].Model;
    foreach(var table in authored.Model.Tables.Where(t=>t.Name.StartsWith("AN ")))
        if(model.Tables.Find(table.Name)==null)model.Tables.Add(table.Clone());
    var target=model.Tables["_Measures"];
    var definitions=authored.Model.Tables["_Measures"].Measures.Where(m=>m.Name.StartsWith("AN ")).ToList();
    var names=definitions.Select(m=>m.Name).ToHashSet();
    foreach(var old in target.Measures.Where(m=>m.Name.StartsWith("AN ") && !names.Contains(m.Name)).ToList()) target.Measures.Remove(old);
    foreach(var source in definitions)
    {
        var measure=target.Measures.Find(source.Name);
        if(measure==null){measure=new Measure{Name=source.Name};target.Measures.Add(measure);}
        measure.Expression=source.Expression;measure.FormatString=source.FormatString;measure.Description=source.Description;measure.DisplayFolder=source.DisplayFolder;
    }
    model.Expressions["AnalyticsGoldDataPath"].Expression="\""+folder.Replace("\\","/").Replace("\"","\"\"")+"\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]";
    foreach(var table in model.Tables.Where(t=>t.Name.StartsWith("AN ")))table.RequestRefresh(RefreshType.Full);
    model.SaveChanges();
    Console.WriteLine("Synced and refreshed analytics measures: "+definitions.Count);
    return;
}

if (args.Length == 3 && args[0] == "--live-bind-ml-build")
{
    using var server = new Server();
    server.Connect("Data Source=localhost:" + args[1]);
    if (server.Databases.Count != 1) throw new InvalidOperationException("Expected one Desktop database");
    using var manifest = System.Text.Json.JsonDocument.Parse(File.ReadAllText(args[2]));
    if (manifest.RootElement.GetProperty("data_origin").GetString() != "SYNTHETIC DEMO MODEL") throw new InvalidOperationException("Not a synthetic ML build");
    var exportPath = Path.GetFullPath(manifest.RootElement.GetProperty("powerbi_path").GetString()!);
    if (!File.Exists(Path.Combine(exportPath,"customer_ml_scores.csv")) || !File.Exists(Path.Combine(exportPath,"model_performance.csv"))) throw new InvalidOperationException("Missing scoring exports");
    var model = server.Databases[0].Model;
    model.Expressions["MLGoldDataPath"].Expression = "\"" + exportPath.Replace("\\","/").Replace("\"","\"\"") + "\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]";
    model.Tables["ML Customer Scores"].RequestRefresh(RefreshType.Full);
    model.Tables["ML Model Performance"].RequestRefresh(RefreshType.Full);
    model.SaveChanges();
    Console.WriteLine("Bound and refreshed ML tables from: " + exportPath);
    return;
}

if (args.Length == 3 && args[0] == "--live-sync-ml-measures")
{
    using var server = new Server();
    server.Connect("Data Source=localhost:" + args[1]);
    if (server.Databases.Count != 1) throw new InvalidOperationException("Expected one Desktop database");
    var authored = Microsoft.AnalysisServices.Tabular.JsonSerializer.DeserializeDatabase(File.ReadAllText(args[2]));
    var target = server.Databases[0].Model.Tables["_Measures"];
    server.Databases[0].Model.Tables["ML Customer Scores"].Columns["Customer Key"].FormatString = "0";
    int count = 0;
    foreach (var sourceMeasure in authored.Model.Tables["_Measures"].Measures.Where(m => m.Name.StartsWith("ML ")))
    {
        var measure = target.Measures[sourceMeasure.Name];
        measure.Expression = sourceMeasure.Expression;
        measure.FormatString = sourceMeasure.FormatString;
        measure.Description = sourceMeasure.Description;
        measure.DisplayFolder = sourceMeasure.DisplayFolder;
        count++;
    }
    server.Databases[0].Model.SaveChanges();
    Console.WriteLine("Updated ML measures: " + count);
    return;
}

if (args.Length == 3 && args[0] == "--live-export")
{
    using var server = new Server();
    server.Connect("Data Source=localhost:" + args[1]);
    if (server.Databases.Count != 1) throw new InvalidOperationException("Expected one Desktop database");
    TmdlSerializer.SerializeDatabaseToFolder(server.Databases[0],Path.GetFullPath(args[2]));
    Console.WriteLine("Native model metadata exported: " + args[2]);
    return;
}

if (args.Length == 3 && args[0] == "--live-query")
{
    using var connection = new Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:" + args[1]);
    connection.Open();
    using var command = connection.CreateCommand();
    command.CommandText = File.ReadAllText(args[2]);
    using var reader = command.ExecuteReader();
    var rows = new List<Dictionary<string, object?>>();
    while (reader.Read())
    {
        var row = new Dictionary<string, object?>();
        for (int i=0; i<reader.FieldCount; i++) row[reader.GetName(i)]=reader.IsDBNull(i)?null:reader.GetValue(i);
        rows.Add(row);
    }
    Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(rows));
    return;
}

if (args.Length == 2 && (args[0] == "--live-inspect" || args[0] == "--live-refresh"))
{
    using var server = new Server();
    server.Connect("Data Source=localhost:" + args[1]);
    if (args[0] == "--live-refresh")
    {
        if (server.Databases.Count != 1) throw new InvalidOperationException("Expected one Desktop database");
        server.Databases[0].Model.RequestRefresh(RefreshType.Full);
        server.Databases[0].Model.SaveChanges();
    }
    foreach (Database db in server.Databases)
        Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new {
            database = db.ID, tables = db.Model.Tables.Select(t => new {
                name = t.Name, partitions = t.Partitions.Select(p => new { name = p.Name, state = p.State.ToString(), error = p.ErrorMessage }),
            }), expressions = db.Model.Expressions.Select(e => new {name=e.Name, expression=e.Expression})
        }));
    return;
}

if (args.Length != 2)
    throw new ArgumentException("Usage: ModelValidator <model.source.json> <TMDL output folder>");
bool checkOnly = args[0] == "--check-folder";
var database = checkOnly ? TmdlSerializer.DeserializeDatabaseFromFolder(args[1]) :
    Microsoft.AnalysisServices.Tabular.JsonSerializer.DeserializeDatabase(File.ReadAllText(args[0]));
if (!checkOnly) TmdlSerializer.SerializeDatabaseToFolder(database, args[1]);
var reloaded = TmdlSerializer.DeserializeDatabaseFromFolder(args[1]);
if (reloaded.Model.Tables.Count != database.Model.Tables.Count || reloaded.Model.Relationships.Count != database.Model.Relationships.Count)
    throw new InvalidOperationException("TMDL round-trip changed object counts.");
foreach (var table in reloaded.Model.Tables)
    foreach (var column in table.Columns)
        if (column.SortByColumn != null && column.SortByColumn.Table != table)
            throw new InvalidOperationException("Invalid sort-by-column reference.");
Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(new {
    status = "PASS",
    tables = reloaded.Model.Tables.Count,
    relationships = reloaded.Model.Relationships.Count,
    measures = reloaded.Model.Tables.Sum(t => t.Measures.Count),
    validation = "Microsoft TOM and TMDL round-trip; no engine refresh or DAX execution"
}));
