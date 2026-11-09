using Microsoft.AspNetCore.Identity;
using MySqlConnector;

namespace AgenciaBackend.Data;

public sealed class DatabaseInitializer(
    DatabaseConnection database,
    IPasswordHasher<string> hasher,
    IConfiguration configuration)
{
    public async Task InitializeAsync()
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        var username = configuration["Admin:Username"] ?? "admin";
        var password = configuration["Admin:Password"] ?? "admin123";
        var hash = hasher.HashPassword(username, password);

        await using var migrate = connection.CreateCommand();
        migrate.CommandText = """
            UPDATE administradores
            SET password_hash = @hash
            WHERE usuario = @usuario AND password_hash = 'cambiado-en-API'
            """;
        migrate.Parameters.AddWithValue("@hash", hash);
        migrate.Parameters.AddWithValue("@usuario", username);
        await migrate.ExecuteNonQueryAsync();

        await using var seed = connection.CreateCommand();
        seed.CommandText = """
            INSERT INTO administradores (nombre, usuario, password_hash)
            SELECT 'Administrador principal', @usuario, @hash
            WHERE NOT EXISTS (SELECT 1 FROM administradores)
            """;
        seed.Parameters.AddWithValue("@usuario", username);
        seed.Parameters.AddWithValue("@hash", hash);
        await seed.ExecuteNonQueryAsync();

        await using var serviceTypeColumn = connection.CreateCommand();
        serviceTypeColumn.CommandText = """
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='servicios' AND COLUMN_NAME='tipo_servicio'
            """;
        if (Convert.ToInt32(await serviceTypeColumn.ExecuteScalarAsync()) == 0)
        {
            await using var addServiceType = connection.CreateCommand();
            addServiceType.CommandText =
                "ALTER TABLE servicios ADD COLUMN tipo_servicio VARCHAR(20) NOT NULL DEFAULT 'Correctivo' AFTER descripcion";
            await addServiceType.ExecuteNonQueryAsync();
        }

        await using var years = connection.CreateCommand();
        years.CommandText = "INSERT IGNORE INTO anos (ano) VALUES (@ano)";
        var yearParameter = years.Parameters.Add("@ano", MySqlDbType.UInt16);
        for (var year = 1980; year <= DateTime.UtcNow.Year + 2; year++)
        {
            yearParameter.Value = year;
            await years.ExecuteNonQueryAsync();
        }
    }
}
