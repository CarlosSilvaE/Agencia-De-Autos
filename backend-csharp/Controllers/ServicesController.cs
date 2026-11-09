using AgenciaBackend.Data;
using AgenciaBackend.Models;
using Microsoft.AspNetCore.Mvc;
using MySqlConnector;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/servicios")]
public class ServicesController(DatabaseConnection database) : ControllerBase
{
    private static readonly HashSet<string> States = new(StringComparer.Ordinal)
        { "En espera", "En proceso", "Finalizado" };

    [HttpGet]
    public async Task<IActionResult> Search([FromQuery] string? folio, [FromQuery] string? propietario)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT s.id_servicio, s.folio, s.tipo_servicio, s.descripcion, s.fecha_ingreso, s.fecha_programada,
                   s.estado, s.costo, v.id_vehiculo, v.placas, v.color, v.vin,
                   v.id_marca, v.id_modelo, v.id_ano, m.nombre AS marca, mo.nombre AS modelo,
                   a.ano, c.id_cliente, c.nombre, c.apellido_paterno, c.apellido_materno,
                   c.telefono, c.email, e.nombre_entrega, e.telefono AS telefono_entrega,
                   e.relacion_propietario, e.observaciones AS observaciones_entrega,
                   p.fecha_programada AS proximo_servicio, p.kilometraje, p.notas AS notas_proximo_servicio
            FROM servicios s
            JOIN vehiculos v ON v.id_vehiculo = s.id_vehiculo
            JOIN marcas m ON m.id_marca = v.id_marca
            JOIN modelos mo ON mo.id_modelo = v.id_modelo
            JOIN anos a ON a.id_ano = v.id_ano
            JOIN clientes c ON c.id_cliente = v.id_cliente
            LEFT JOIN entregas e ON e.id_entrega = (
                SELECT MAX(e2.id_entrega) FROM entregas e2 WHERE e2.id_servicio = s.id_servicio
            )
            LEFT JOIN proximos_servicios p ON p.id_proximo_servicio = (
                SELECT MAX(p2.id_proximo_servicio) FROM proximos_servicios p2 WHERE p2.id_servicio = s.id_servicio
            )
            WHERE (@folio = '' OR s.folio = @folio)
              AND (@propietario = '' OR CONCAT_WS(' ', c.nombre, c.apellido_paterno, c.apellido_materno) LIKE CONCAT('%', @propietario, '%'))
            ORDER BY s.fecha_ingreso DESC LIMIT 200
            """;
        command.Parameters.AddWithValue("@folio", folio?.Trim() ?? "");
        command.Parameters.AddWithValue("@propietario", propietario?.Trim() ?? "");
        await using var reader = await command.ExecuteReaderAsync();
        var rows = new List<Dictionary<string, object?>>();
        while (await reader.ReadAsync())
            rows.Add(Enumerable.Range(0, reader.FieldCount).ToDictionary(reader.GetName, i => reader.IsDBNull(i) ? null : reader.GetValue(i)));
        return Ok(rows);
    }

    [HttpGet("proximos")]
    public async Task<IActionResult> Upcoming([FromQuery] string? folio, [FromQuery] string? propietario)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT p.*, s.folio, v.placas, c.nombre, c.apellido_paterno, c.apellido_materno
            FROM proximos_servicios p
            JOIN servicios s ON s.id_servicio=p.id_servicio
            JOIN vehiculos v ON v.id_vehiculo=s.id_vehiculo
            JOIN clientes c ON c.id_cliente=v.id_cliente
            WHERE (@folio='' OR s.folio=@folio)
              AND (@propietario='' OR CONCAT_WS(' ', c.nombre,c.apellido_paterno,c.apellido_materno) LIKE CONCAT('%',@propietario,'%'))
            ORDER BY p.fecha_programada
            """;
        command.Parameters.AddWithValue("@folio", folio?.Trim() ?? "");
        command.Parameters.AddWithValue("@propietario", propietario?.Trim() ?? "");
        await using var reader = await command.ExecuteReaderAsync();
        var rows = new List<Dictionary<string, object?>>();
        while (await reader.ReadAsync())
            rows.Add(Enumerable.Range(0, reader.FieldCount).ToDictionary(reader.GetName, i => reader.IsDBNull(i) ? null : reader.GetValue(i)));
        return Ok(rows);
    }

    [HttpGet("{folio}/refacciones")]
    public async Task<IActionResult> Parts(string folio)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT sr.id_refaccion, sr.cantidad, sr.precio_unitario
            FROM servicio_refaccion sr JOIN servicios s ON s.id_servicio=sr.id_servicio
            WHERE s.folio=@folio
            """;
        command.Parameters.AddWithValue("@folio", folio);
        await using var reader = await command.ExecuteReaderAsync();
        var rows = new List<Dictionary<string, object>>();
        while (await reader.ReadAsync())
            rows.Add(new Dictionary<string, object>
            {
                ["id_refaccion"] = reader.GetInt32("id_refaccion"),
                ["cantidad"] = reader.GetInt32("cantidad"),
                ["precio_unitario"] = reader.GetDecimal("precio_unitario")
            });
        return Ok(rows);
    }

    [HttpPost]
    public async Task<IActionResult> Create(ServiceInput input)
    {
        var validation = Validate(input);
        if (validation is not null) return BadRequest(new { message = validation });
        var folio = string.IsNullOrWhiteSpace(input.Folio)
            ? $"SRV-{DateTime.UtcNow:yyyyMMddHHmmssfff}-{Guid.NewGuid().ToString("N")[..6]}"
            : input.Folio.Trim();

        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var transaction = await connection.BeginTransactionAsync();
        try
        {
            var clientId = await SaveClient(connection, transaction, input.Cliente);
            var vehicleId = await SaveVehicle(connection, transaction, input.Vehiculo, clientId);
            await using var command = connection.CreateCommand();
            command.Transaction = transaction;
            command.CommandText = """
                INSERT INTO servicios (folio,id_vehiculo,tipo_servicio,descripcion,estado,costo)
                VALUES (@folio,@vehiculo,@tipo,@descripcion,@estado,@costo)
                """;
            command.Parameters.AddWithValue("@folio", folio);
            command.Parameters.AddWithValue("@vehiculo", vehicleId);
            command.Parameters.AddWithValue("@tipo", input.TipoServicio);
            command.Parameters.AddWithValue("@descripcion", input.Descripcion.Trim());
            command.Parameters.AddWithValue("@estado", input.Estado);
            command.Parameters.AddWithValue("@costo", input.Costo);
            await command.ExecuteNonQueryAsync();
            var serviceId = (uint)command.LastInsertedId;
            await SaveRelations(connection, transaction, serviceId, input);
            await transaction.CommitAsync();
            return CreatedAtAction(nameof(Search), new { folio }, new { folio });
        }
        catch (MySqlException exception) when (exception.Number is 1062 or 1452)
        {
            await transaction.RollbackAsync();
            return Conflict(new { message = "El folio o las placas ya existen, o se seleccionó una referencia inválida." });
        }
        catch (InvalidOperationException exception)
        {
            await transaction.RollbackAsync();
            return Conflict(new { message = exception.Message });
        }
        catch
        {
            await transaction.RollbackAsync();
            throw;
        }
    }

    [HttpPut("{folio}")]
    public async Task<IActionResult> Update(string folio, ServiceInput input)
    {
        var validation = Validate(input);
        if (validation is not null) return BadRequest(new { message = validation });
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var transaction = await connection.BeginTransactionAsync();
        try
        {
            var serviceId = await FindServiceId(connection, transaction, folio);
            if (serviceId is null) return NotFound();
            var clientId = await SaveClient(connection, transaction, input.Cliente);
            var vehicleId = await SaveVehicle(connection, transaction, input.Vehiculo, clientId);
            await using var update = connection.CreateCommand();
            update.Transaction = transaction;
            update.CommandText = """
                UPDATE servicios SET id_vehiculo=@vehiculo, tipo_servicio=@tipo, descripcion=@descripcion,
                    estado=@estado, costo=@costo WHERE id_servicio=@id
                """;
            update.Parameters.AddWithValue("@vehiculo", vehicleId);
            update.Parameters.AddWithValue("@tipo", input.TipoServicio);
            update.Parameters.AddWithValue("@descripcion", input.Descripcion.Trim());
            update.Parameters.AddWithValue("@estado", input.Estado);
            update.Parameters.AddWithValue("@costo", input.Costo);
            update.Parameters.AddWithValue("@id", serviceId);
            await update.ExecuteNonQueryAsync();
            await SaveRelations(connection, transaction, serviceId.Value, input);
            await transaction.CommitAsync();
            return NoContent();
        }
        catch (MySqlException exception) when (exception.Number is 1062 or 1452)
        {
            await transaction.RollbackAsync();
            return Conflict(new { message = "Las placas ya existen o se seleccionó una referencia inválida." });
        }
        catch (InvalidOperationException exception)
        {
            await transaction.RollbackAsync();
            return Conflict(new { message = exception.Message });
        }
        catch
        {
            await transaction.RollbackAsync();
            throw;
        }
    }

    [HttpDelete("{folio}")]
    public async Task<IActionResult> Delete(string folio)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var transaction = await connection.BeginTransactionAsync();
        var serviceId = await FindServiceId(connection, transaction, folio);
        if (serviceId is null) return NotFound();
        await Execute(connection, transaction, "UPDATE refacciones r JOIN servicio_refaccion sr ON sr.id_refaccion=r.id_refaccion SET r.cantidad=r.cantidad+sr.cantidad WHERE sr.id_servicio=@id", serviceId.Value);
        await Execute(connection, transaction, "DELETE FROM servicio_refaccion WHERE id_servicio=@id", serviceId.Value);
        await Execute(connection, transaction, "DELETE FROM entregas WHERE id_servicio=@id", serviceId.Value);
        await Execute(connection, transaction, "DELETE FROM proximos_servicios WHERE id_servicio=@id", serviceId.Value);
        await Execute(connection, transaction, "DELETE FROM servicios WHERE id_servicio=@id", serviceId.Value);
        await transaction.CommitAsync();
        return NoContent();
    }

    [HttpPatch("{folio}/estado")]
    public async Task<IActionResult> UpdateStatus(string folio, [FromBody] StatusInput input)
    {
        if (!States.Contains(input.Estado))
            return BadRequest(new { message = "Estado inválido." });
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = "UPDATE servicios SET estado=@estado WHERE folio=@folio";
        command.Parameters.AddWithValue("@estado", input.Estado);
        command.Parameters.AddWithValue("@folio", folio);
        if (await command.ExecuteNonQueryAsync() != 0) return NoContent();
        await using var exists = connection.CreateCommand();
        exists.CommandText = "SELECT COUNT(*) FROM servicios WHERE folio=@folio";
        exists.Parameters.AddWithValue("@folio", folio);
        return Convert.ToInt32(await exists.ExecuteScalarAsync()) == 0 ? NotFound() : NoContent();
    }

    public sealed record StatusInput(string Estado);

    private static string? Validate(ServiceInput input)
    {
        if (string.IsNullOrWhiteSpace(input.Descripcion)) return "La descripción es obligatoria.";
        if (input.TipoServicio is not ("Preventivo" or "Correctivo")) return "El tipo de servicio debe ser Preventivo o Correctivo.";
        if (!States.Contains(input.Estado)) return "El estado debe ser En espera, En proceso o Finalizado.";
        if (input.Costo < 0) return "El costo no puede ser negativo.";
        if (input.Cliente is null || string.IsNullOrWhiteSpace(input.Cliente.Nombre) || string.IsNullOrWhiteSpace(input.Cliente.ApellidoPaterno))
            return "Se requiere el nombre y apellido del propietario.";
        if (input.Vehiculo is null || string.IsNullOrWhiteSpace(input.Vehiculo.Placas))
            return "Se requieren las placas del vehículo.";
        if (input.Entrega is null || string.IsNullOrWhiteSpace(input.Entrega.Nombre))
            return "Se requiere identificar a la persona que entrega el vehículo.";
        if (input.Refacciones?.Any(part => part.Cantidad <= 0 || part.PrecioUnitario < 0) == true)
            return "Las cantidades deben ser positivas y los precios no negativos.";
        return null;
    }

    private static async Task<long> SaveClient(MySqlConnection connection, MySqlTransaction transaction, ClientInput input)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        if (input.Id is null)
            command.CommandText = "INSERT INTO clientes (nombre,apellido_paterno,apellido_materno,telefono,email) VALUES (@nombre,@ap,@am,@tel,@email)";
        else
        {
            command.CommandText = "UPDATE clientes SET nombre=@nombre,apellido_paterno=@ap,apellido_materno=@am,telefono=@tel,email=@email WHERE id_cliente=@id AND activo=1";
            command.Parameters.AddWithValue("@id", input.Id);
        }
        command.Parameters.AddWithValue("@nombre", input.Nombre.Trim());
        command.Parameters.AddWithValue("@ap", input.ApellidoPaterno.Trim());
        command.Parameters.AddWithValue("@am", (object?)input.ApellidoMaterno ?? DBNull.Value);
        command.Parameters.AddWithValue("@tel", (object?)input.Telefono ?? DBNull.Value);
        command.Parameters.AddWithValue("@email", (object?)input.Email ?? DBNull.Value);
        var affected = await command.ExecuteNonQueryAsync();
        if (input.Id is not null && affected == 0 &&
            !await Exists(connection, transaction, "SELECT COUNT(*) FROM clientes WHERE id_cliente=@id AND activo=1", input.Id.Value))
            throw new InvalidOperationException("El propietario seleccionado ya no existe.");
        return input.Id ?? command.LastInsertedId;
    }

    private static async Task<long> SaveVehicle(MySqlConnection connection, MySqlTransaction transaction, VehicleInput input, long clientId)
    {
        await using (var validation = connection.CreateCommand())
        {
            validation.Transaction = transaction;
            validation.CommandText = "SELECT COUNT(*) FROM modelos WHERE id_modelo=@modelo AND id_marca=@marca AND activo=1";
            validation.Parameters.AddWithValue("@modelo", input.IdModelo);
            validation.Parameters.AddWithValue("@marca", input.IdMarca);
            if (Convert.ToInt32(await validation.ExecuteScalarAsync()) == 0)
                throw new InvalidOperationException("El modelo seleccionado no pertenece a la marca.");
        }
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        if (input.Id is null)
            command.CommandText = "INSERT INTO vehiculos (id_cliente,id_marca,id_modelo,id_ano,placas,color,vin) VALUES (@cliente,@marca,@modelo,@ano,@placas,@color,@vin)";
        else
        {
            command.CommandText = "UPDATE vehiculos SET id_cliente=@cliente,id_marca=@marca,id_modelo=@modelo,id_ano=@ano,placas=@placas,color=@color,vin=@vin WHERE id_vehiculo=@id AND activo=1";
            command.Parameters.AddWithValue("@id", input.Id);
        }
        command.Parameters.AddWithValue("@cliente", clientId);
        command.Parameters.AddWithValue("@marca", input.IdMarca);
        command.Parameters.AddWithValue("@modelo", input.IdModelo);
        command.Parameters.AddWithValue("@ano", input.IdAno);
        command.Parameters.AddWithValue("@placas", input.Placas.Trim());
        command.Parameters.AddWithValue("@color", (object?)input.Color ?? DBNull.Value);
        command.Parameters.AddWithValue("@vin", (object?)input.Vin ?? DBNull.Value);
        var affected = await command.ExecuteNonQueryAsync();
        if (input.Id is not null && affected == 0 &&
            !await Exists(connection, transaction, "SELECT COUNT(*) FROM vehiculos WHERE id_vehiculo=@id AND activo=1", input.Id.Value))
            throw new InvalidOperationException("El vehículo seleccionado ya no existe.");
        return input.Id ?? command.LastInsertedId;
    }

    private static async Task SaveRelations(MySqlConnection connection, MySqlTransaction transaction, long serviceId, ServiceInput input)
    {
        await Execute(connection, transaction, "UPDATE refacciones r JOIN servicio_refaccion sr ON sr.id_refaccion=r.id_refaccion SET r.cantidad=r.cantidad+sr.cantidad WHERE sr.id_servicio=@id", serviceId);
        await Execute(connection, transaction, "DELETE FROM servicio_refaccion WHERE id_servicio=@id", serviceId);
        foreach (var part in input.Refacciones ?? [])
        {
            await using var inventory = connection.CreateCommand();
            inventory.Transaction = transaction;
            inventory.CommandText = "UPDATE refacciones SET cantidad=cantidad-@cantidad WHERE id_refaccion=@id AND activo=1 AND cantidad>=@cantidad";
            inventory.Parameters.AddWithValue("@cantidad", part.Cantidad);
            inventory.Parameters.AddWithValue("@id", part.IdRefaccion);
            if (await inventory.ExecuteNonQueryAsync() == 0)
                throw new InvalidOperationException("No hay inventario suficiente para una refacción seleccionada.");

            await using var line = connection.CreateCommand();
            line.Transaction = transaction;
            line.CommandText = "INSERT INTO servicio_refaccion (id_servicio,id_refaccion,cantidad,precio_unitario) VALUES (@servicio,@refaccion,@cantidad,@precio)";
            line.Parameters.AddWithValue("@servicio", serviceId);
            line.Parameters.AddWithValue("@refaccion", part.IdRefaccion);
            line.Parameters.AddWithValue("@cantidad", part.Cantidad);
            line.Parameters.AddWithValue("@precio", part.PrecioUnitario);
            await line.ExecuteNonQueryAsync();
        }

        await Execute(connection, transaction, "DELETE FROM entregas WHERE id_servicio=@id", serviceId);
        await using (var delivery = connection.CreateCommand())
        {
            delivery.Transaction = transaction;
            delivery.CommandText = """
                INSERT INTO entregas (id_servicio,nombre_entrega,telefono,relacion_propietario,observaciones)
                VALUES (@id,@nombre,@telefono,@relacion,@observaciones)
                """;
            delivery.Parameters.AddWithValue("@id", serviceId);
            delivery.Parameters.AddWithValue("@nombre", input.Entrega.Nombre.Trim());
            delivery.Parameters.AddWithValue("@telefono", (object?)input.Entrega.Telefono ?? DBNull.Value);
            delivery.Parameters.AddWithValue("@relacion", (object?)input.Entrega.RelacionPropietario ?? DBNull.Value);
            delivery.Parameters.AddWithValue("@observaciones", (object?)input.Entrega.Observaciones ?? DBNull.Value);
            await delivery.ExecuteNonQueryAsync();
        }

        await Execute(connection, transaction, "DELETE FROM proximos_servicios WHERE id_servicio=@id", serviceId);
        if (input.ProximoServicio is not null)
        {
            await using var next = connection.CreateCommand();
            next.Transaction = transaction;
            next.CommandText = "INSERT INTO proximos_servicios (id_servicio,fecha_programada,kilometraje,notas) VALUES (@id,@fecha,@km,@notas)";
            next.Parameters.AddWithValue("@id", serviceId);
            next.Parameters.AddWithValue("@fecha", input.ProximoServicio.FechaProgramada.ToDateTime(TimeOnly.MinValue));
            next.Parameters.AddWithValue("@km", (object?)input.ProximoServicio.Kilometraje ?? DBNull.Value);
            next.Parameters.AddWithValue("@notas", (object?)input.ProximoServicio.Notas ?? DBNull.Value);
            await next.ExecuteNonQueryAsync();
        }
    }

    private static async Task<long?> FindServiceId(MySqlConnection connection, MySqlTransaction transaction, string folio)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "SELECT id_servicio FROM servicios WHERE folio=@folio";
        command.Parameters.AddWithValue("@folio", folio);
        var result = await command.ExecuteScalarAsync();
        return result is null or DBNull ? null : Convert.ToInt64(result);
    }

    private static async Task<bool> Exists(MySqlConnection connection, MySqlTransaction transaction, string sql, long id)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = sql;
        command.Parameters.AddWithValue("@id", id);
        return Convert.ToInt32(await command.ExecuteScalarAsync()) > 0;
    }

    private static async Task Execute(MySqlConnection connection, MySqlTransaction transaction, string sql, long id)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = sql;
        command.Parameters.AddWithValue("@id", id);
        await command.ExecuteNonQueryAsync();
    }
}
