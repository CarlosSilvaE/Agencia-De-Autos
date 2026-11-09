using AgenciaBackend.Data;
using Microsoft.AspNetCore.Mvc;
using MySqlConnector;
using System.Text.Json;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/catalogos/{catalogo}")]
public class CatalogController(DatabaseConnection database) : ControllerBase
{
    private sealed record CatalogDefinition(string Table, string Id, string[] Fields);

    private static readonly IReadOnlyDictionary<string, CatalogDefinition> Catalogs =
        new Dictionary<string, CatalogDefinition>(StringComparer.OrdinalIgnoreCase)
        {
            ["marcas"] = new("marcas", "id_marca", ["nombre"]),
            ["modelos"] = new("modelos", "id_modelo", ["id_marca", "nombre"]),
            ["anos"] = new("anos", "id_ano", ["ano"]),
            ["refacciones"] = new("refacciones", "id_refaccion", ["nombre", "sku", "cantidad", "precio"])
        };

    [HttpGet]
    public async Task<IActionResult> List(string catalogo)
    {
        if (!Catalogs.TryGetValue(catalogo, out var definition))
            return NotFound(new { message = "Catálogo desconocido." });

        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = $"SELECT * FROM `{definition.Table}` WHERE activo = 1 ORDER BY `{definition.Id}` DESC";
        await using var reader = await command.ExecuteReaderAsync();
        var rows = new List<Dictionary<string, object?>>();
        while (await reader.ReadAsync())
            rows.Add(Enumerable.Range(0, reader.FieldCount).ToDictionary(
                reader.GetName,
                i => reader.IsDBNull(i) ? null : reader.GetValue(i)));
        return Ok(rows);
    }

    [HttpPost]
    public Task<IActionResult> Create(string catalogo, [FromBody] Dictionary<string, object?> values) =>
        Save(catalogo, null, values);

    [HttpPut("{id:int}")]
    public Task<IActionResult> Update(string catalogo, int id, [FromBody] Dictionary<string, object?> values) =>
        Save(catalogo, id, values);

    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(string catalogo, int id)
    {
        if (!Catalogs.TryGetValue(catalogo, out var definition))
            return NotFound(new { message = "Catálogo desconocido." });
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = $"UPDATE `{definition.Table}` SET activo = 0 WHERE `{definition.Id}` = @id";
        command.Parameters.AddWithValue("@id", id);
        return await command.ExecuteNonQueryAsync() == 0 ? NotFound() : NoContent();
    }

    private async Task<IActionResult> Save(string catalogo, int? id, Dictionary<string, object?> values)
    {
        if (!Catalogs.TryGetValue(catalogo, out var definition))
            return NotFound(new { message = "Catálogo desconocido." });
        foreach (var field in definition.Fields)
            if (!values.TryGetValue(field, out var value) || value is null || string.IsNullOrWhiteSpace(value.ToString()))
                return BadRequest(new { message = $"El campo {field} es obligatorio." });

        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        if (id is null)
        {
            command.CommandText = $"INSERT INTO `{definition.Table}` ({string.Join(", ", definition.Fields.Select(f => $"`{f}`"))}) VALUES ({string.Join(", ", definition.Fields.Select(f => $"@{f}"))})";
        }
        else
        {
            command.CommandText = $"UPDATE `{definition.Table}` SET {string.Join(", ", definition.Fields.Select(f => $"`{f}` = @{f}"))} WHERE `{definition.Id}` = @id AND activo = 1";
            command.Parameters.AddWithValue("@id", id);
        }
        foreach (var field in definition.Fields)
            command.Parameters.AddWithValue($"@{field}", GetValue(values[field]));

        try
        {
            var affected = await command.ExecuteNonQueryAsync();
            if (id is not null && affected == 0)
            {
                await using var exists = connection.CreateCommand();
                exists.CommandText = $"SELECT COUNT(*) FROM `{definition.Table}` WHERE `{definition.Id}`=@id AND activo=1";
                exists.Parameters.AddWithValue("@id", id);
                if (Convert.ToInt32(await exists.ExecuteScalarAsync()) == 0)
                    return NotFound();
            }
            return id is null ? Ok(new { id = command.LastInsertedId }) : NoContent();
        }
        catch (MySqlException exception) when (exception.Number is 1062 or 1452)
        {
            return Conflict(new { message = "El valor ya existe o una referencia seleccionada no es válida." });
        }
    }

    private static object GetValue(object? value) => value switch
    {
        null => DBNull.Value,
        JsonElement element when element.ValueKind == JsonValueKind.Number && element.TryGetInt64(out var number) => number,
        JsonElement element when element.ValueKind == JsonValueKind.Number => element.GetDecimal(),
        JsonElement element when element.ValueKind == JsonValueKind.String => element.GetString()!,
        JsonElement element when element.ValueKind is JsonValueKind.True or JsonValueKind.False => element.GetBoolean(),
        JsonElement element when element.ValueKind == JsonValueKind.Null => DBNull.Value,
        _ => value
    };
}
