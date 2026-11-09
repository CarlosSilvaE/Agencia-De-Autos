using AgenciaBackend.Data;
using Microsoft.AspNetCore.Mvc;
using MySqlConnector;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/vehiculos")]
public class VehiclesController(DatabaseConnection database) : ControllerBase
{
    public sealed record VehicleInput(int IdCliente, int IdMarca, int IdModelo, int IdAno, string Placas, string? Color, string? Vin);

    [HttpGet]
    public async Task<IActionResult> List()
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT v.*, c.nombre, c.apellido_paterno, c.apellido_materno, c.telefono, c.email, m.nombre AS marca,
                   mo.nombre AS modelo, a.ano
            FROM vehiculos v JOIN clientes c ON c.id_cliente=v.id_cliente
            JOIN marcas m ON m.id_marca=v.id_marca JOIN modelos mo ON mo.id_modelo=v.id_modelo
            JOIN anos a ON a.id_ano=v.id_ano
            WHERE v.activo=1 AND c.activo=1 ORDER BY v.placas
            """;
        await using var reader = await command.ExecuteReaderAsync();
        var rows = new List<Dictionary<string, object?>>();
        while (await reader.ReadAsync())
            rows.Add(Enumerable.Range(0, reader.FieldCount).ToDictionary(reader.GetName, i => reader.IsDBNull(i) ? null : reader.GetValue(i)));
        return Ok(rows);
    }

    [HttpPost]
    public async Task<IActionResult> Create(VehicleInput input) => await Save(null, input);

    [HttpPut("{id:int}")]
    public async Task<IActionResult> Update(int id, VehicleInput input) => await Save(id, input);

    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = "UPDATE vehiculos SET activo=0 WHERE id_vehiculo=@id";
        command.Parameters.AddWithValue("@id", id);
        try { return await command.ExecuteNonQueryAsync() == 0 ? NotFound() : NoContent(); }
        catch (MySqlException exception) when (exception.Number == 1451)
        {
            return Conflict(new { message = "No se puede desactivar un vehículo con servicios asociados." });
        }
    }

    private async Task<IActionResult> Save(int? id, VehicleInput input)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using (var validation = connection.CreateCommand())
        {
            validation.CommandText = "SELECT COUNT(*) FROM modelos WHERE id_modelo=@modelo AND id_marca=@marca AND activo=1";
            validation.Parameters.AddWithValue("@modelo", input.IdModelo);
            validation.Parameters.AddWithValue("@marca", input.IdMarca);
            if (Convert.ToInt32(await validation.ExecuteScalarAsync()) == 0)
                return BadRequest(new { message = "El modelo seleccionado no pertenece a la marca." });
        }
        await using var command = connection.CreateCommand();
        if (id is null)
            command.CommandText = "INSERT INTO vehiculos (id_cliente,id_marca,id_modelo,id_ano,placas,color,vin) VALUES (@cliente,@marca,@modelo,@ano,@placas,@color,@vin)";
        else
        {
            command.CommandText = "UPDATE vehiculos SET id_cliente=@cliente,id_marca=@marca,id_modelo=@modelo,id_ano=@ano,placas=@placas,color=@color,vin=@vin WHERE id_vehiculo=@id AND activo=1";
            command.Parameters.AddWithValue("@id", id);
        }
        command.Parameters.AddWithValue("@cliente", input.IdCliente);
        command.Parameters.AddWithValue("@marca", input.IdMarca);
        command.Parameters.AddWithValue("@modelo", input.IdModelo);
        command.Parameters.AddWithValue("@ano", input.IdAno);
        command.Parameters.AddWithValue("@placas", input.Placas.Trim());
        command.Parameters.AddWithValue("@color", (object?)input.Color ?? DBNull.Value);
        command.Parameters.AddWithValue("@vin", (object?)input.Vin ?? DBNull.Value);
        try
        {
            var affected = await command.ExecuteNonQueryAsync();
            if (id is not null && affected == 0)
            {
                await using var exists = connection.CreateCommand();
                exists.CommandText = "SELECT COUNT(*) FROM vehiculos WHERE id_vehiculo=@id AND activo=1";
                exists.Parameters.AddWithValue("@id", id);
                if (Convert.ToInt32(await exists.ExecuteScalarAsync()) == 0) return NotFound();
            }
            return id is null ? Ok(new { id = command.LastInsertedId }) : NoContent();
        }
        catch (MySqlException exception) when (exception.Number is 1062 or 1452)
        {
            return Conflict(new { message = "Las placas deben ser únicas y cliente, marca, modelo y año deben existir." });
        }
    }
}
