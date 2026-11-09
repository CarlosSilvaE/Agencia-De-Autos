using AgenciaBackend.Data;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using MySqlConnector;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/administradores")]
public class AdminsController(DatabaseConnection database, IPasswordHasher<string> hasher) : ControllerBase
{
    public sealed record AdminRequest(string Nombre, string Usuario, string? Password, bool Activo = true);

    [HttpGet]
    public async Task<IActionResult> List()
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = "SELECT id_administrador, nombre, usuario, activo FROM administradores ORDER BY nombre";
        await using var reader = await command.ExecuteReaderAsync();
        var rows = new List<Dictionary<string, object>>();
        while (await reader.ReadAsync())
            rows.Add(Enumerable.Range(0, reader.FieldCount).ToDictionary(reader.GetName, i => reader.GetValue(i)));
        return Ok(rows);
    }

    [HttpPost]
    public async Task<IActionResult> Create(AdminRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.Nombre) || string.IsNullOrWhiteSpace(request.Usuario) ||
            string.IsNullOrWhiteSpace(request.Password) || request.Password.Length < 8)
            return BadRequest(new { message = "Nombre, usuario y contraseña de al menos 8 caracteres son obligatorios." });
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText = "INSERT INTO administradores (nombre,usuario,password_hash,activo) VALUES (@nombre,@usuario,@hash,@activo)";
        command.Parameters.AddWithValue("@nombre", request.Nombre.Trim());
        command.Parameters.AddWithValue("@usuario", request.Usuario.Trim());
        command.Parameters.AddWithValue("@hash", hasher.HashPassword(request.Usuario, request.Password));
        command.Parameters.AddWithValue("@activo", request.Activo);
        try { await command.ExecuteNonQueryAsync(); return Ok(new { id = command.LastInsertedId }); }
        catch (MySqlException exception) when (exception.Number == 1062)
        {
            return Conflict(new { message = "Ese nombre de usuario ya está registrado." });
        }
    }

    [HttpPut("{id:int}")]
    public async Task<IActionResult> Update(int id, AdminRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.Nombre) || string.IsNullOrWhiteSpace(request.Usuario) ||
            (request.Password is not null && request.Password.Length < 8))
            return BadRequest(new { message = "Nombre y usuario son obligatorios; la contraseña debe tener al menos 8 caracteres." });
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        if (!request.Activo)
        {
            await using var count = connection.CreateCommand();
            count.CommandText = "SELECT COUNT(*) FROM administradores WHERE activo=1";
            if (Convert.ToInt32(await count.ExecuteScalarAsync()) <= 1)
                return Conflict(new { message = "Debe permanecer al menos un administrador activo." });
        }
        await using var command = connection.CreateCommand();
        command.CommandText = request.Password is null
            ? "UPDATE administradores SET nombre=@nombre,usuario=@usuario,activo=@activo WHERE id_administrador=@id"
            : "UPDATE administradores SET nombre=@nombre,usuario=@usuario,password_hash=@hash,activo=@activo WHERE id_administrador=@id";
        command.Parameters.AddWithValue("@id", id);
        command.Parameters.AddWithValue("@nombre", request.Nombre.Trim());
        command.Parameters.AddWithValue("@usuario", request.Usuario.Trim());
        command.Parameters.AddWithValue("@activo", request.Activo);
        if (request.Password is not null)
            command.Parameters.AddWithValue("@hash", hasher.HashPassword(request.Usuario, request.Password));
        try
        {
            if (await command.ExecuteNonQueryAsync() != 0) return NoContent();
            await using var exists = connection.CreateCommand();
            exists.CommandText = "SELECT COUNT(*) FROM administradores WHERE id_administrador=@id";
            exists.Parameters.AddWithValue("@id", id);
            return Convert.ToInt32(await exists.ExecuteScalarAsync()) == 0 ? NotFound() : NoContent();
        }
        catch (MySqlException exception) when (exception.Number == 1062)
        {
            return Conflict(new { message = "Ese nombre de usuario ya está registrado." });
        }
    }

    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete(int id)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var transaction = await connection.BeginTransactionAsync();
        await using var count = connection.CreateCommand();
        count.Transaction = transaction;
        count.CommandText = "SELECT COUNT(*) FROM administradores WHERE activo=1";
        var active = Convert.ToInt32(await count.ExecuteScalarAsync());
        if (active <= 1) return Conflict(new { message = "Debe permanecer al menos un administrador activo." });
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = "UPDATE administradores SET activo=0 WHERE id_administrador=@id AND activo=1";
        command.Parameters.AddWithValue("@id", id);
        var affected = await command.ExecuteNonQueryAsync();
        if (affected == 0) return NotFound();
        await transaction.CommitAsync();
        return NoContent();
    }
}
