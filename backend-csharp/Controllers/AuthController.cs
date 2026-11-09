using AgenciaBackend.Data;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Identity;
using MySqlConnector;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController(DatabaseConnection database, IPasswordHasher<string> hasher) : ControllerBase
{
    public sealed record LoginRequest(string Username, string Password);

    [HttpPost("login")]
    public async Task<IActionResult> Login(LoginRequest request)
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        await connection.OpenAsync();
        await using var command = connection.CreateCommand();
        command.CommandText =
            "SELECT password_hash FROM administradores WHERE usuario = @usuario AND activo = 1 LIMIT 1";
        command.Parameters.AddWithValue("@usuario", request.Username);

        var storedHash = await command.ExecuteScalarAsync() as string;
        if (storedHash is null ||
            hasher.VerifyHashedPassword(request.Username, storedHash, request.Password)
                == PasswordVerificationResult.Failed)
            return Unauthorized(new { authenticated = false });

        return Ok(new { authenticated = true, user = request.Username });
    }
}
