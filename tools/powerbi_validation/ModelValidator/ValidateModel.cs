using Microsoft.AnalysisServices.Tabular;

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
