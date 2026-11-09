using AgenciaBackend.Data;
using MySqlConnector;

namespace AgenciaBackend.Services;

public class DashboardService(DatabaseConnection database, DashboardStrategies strategies)
{
    public async Task<object> GetAsync(string filter, DateOnly? date)
    {
        var strategy = strategies.Create(filter);
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = strategy.Sql;
        if (strategy is DailyDashboardStrategy)
            command.Parameters.AddWithValue("@fecha", (date ?? DateOnly.FromDateTime(DateTime.Today)).ToDateTime(TimeOnly.MinValue));
        await using var reader = await command.ExecuteReaderAsync();
        var result = new List<Dictionary<string, object>>();
        while (await reader.ReadAsync())
            result.Add(new Dictionary<string, object>
            {
                ["estado"] = reader.GetString("estado"),
                ["cantidad"] = reader.GetInt64("cantidad")
            });
        return result;
    }
}
