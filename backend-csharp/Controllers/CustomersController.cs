using AgenciaBackend.Data;
using Microsoft.AspNetCore.Mvc;
using MySqlConnector;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/clientes")]
public class CustomersController(DatabaseConnection database) : ControllerBase
{
    public sealed record CustomerInput(string Nombre, string ApellidoPaterno, string? ApellidoMaterno, string? Telefono, string? Email);

    [HttpGet]
    public async Task<IActionResult> List()
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT * FROM clientes WHERE activo = 1 ORDER BY nombre, apellido_paterno";
        await using var reader = await command.ExecuteReaderAsync();
        var rows = new List<Dictionary<string, object?>>();
        while (await reader.ReadAsync())
            rows.Add(Enumerable.Range(0, reader.FieldCount).ToDictionary(reader.GetName, i => reader.IsDBNull(i) ? null : reader.GetValue(i)));
        return Ok(rows);
    }

    [HttpPost]
    public async Task<IActionResult> Create(CustomerInput input) => await Save(null, input);

    [HttpPut("{id:int}")]
    public async Task<IActionResult> Update(int id, CustomerInput input) => await Save(id, input);

    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = "UPDATE clientes SET activo = 0 WHERE id_cliente = @id";
        command.Parameters.AddWithValue("@id", id);
        try { return await command.ExecuteNonQueryAsync() == 0 ? NotFound() : NoContent(); }
        catch (MySqlException exception) when (exception.Number == 1451)
        {
            return Conflict(new { message = "No se puede desactivar un cliente con vehículos asociados." });
        }
    }

    private async Task<IActionResult> Save(int? id, CustomerInput input)
    {
        if (string.IsNullOrWhiteSpace(input.Nombre) || string.IsNullOrWhiteSpace(input.ApellidoPaterno))
            return BadRequest(new { message = "Nombre y apellido paterno son obligatorios." });
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        if (id is null)
            command.CommandText = "INSERT INTO clientes (nombre, apellido_paterno, apellido_materno, telefono, email) VALUES (@nombre, @ap, @am, @telefono, @email)";
        else
        {
            command.CommandText = "UPDATE clientes SET nombre=@nombre, apellido_paterno=@ap, apellido_materno=@am, telefono=@telefono, email=@email WHERE id_cliente=@id AND activo=1";
            command.Parameters.AddWithValue("@id", id);
        }
        command.Parameters.AddWithValue("@nombre", input.Nombre.Trim());
        command.Parameters.AddWithValue("@ap", input.ApellidoPaterno.Trim());
        command.Parameters.AddWithValue("@am", (object?)input.ApellidoMaterno ?? DBNull.Value);
        command.Parameters.AddWithValue("@telefono", (object?)input.Telefono ?? DBNull.Value);
        command.Parameters.AddWithValue("@email", (object?)input.Email ?? DBNull.Value);
        var affected = await command.ExecuteNonQueryAsync();
        if (id is not null && affected == 0)
        {
            await using var exists = connection.CreateCommand();
            exists.CommandText = "SELECT COUNT(*) FROM clientes WHERE id_cliente=@id AND activo=1";
            exists.Parameters.AddWithValue("@id", id);
            if (Convert.ToInt32(await exists.ExecuteScalarAsync()) == 0) return NotFound();
        }
        return id is null ? Ok(new { id = command.LastInsertedId }) : NoContent();
    }
}
