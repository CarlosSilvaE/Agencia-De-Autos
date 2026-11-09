using AgenciaBackend.Data;
using Microsoft.AspNetCore.Mvc;
using MySqlConnector;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class HealthController(DatabaseConnection database) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> Get()
    {
        await using var connection = new MySqlConnection(database.ConnectionString);
        try
        {
            await connection.OpenAsync();
            return Ok(new { status = "healthy", service = "backend-csharp", database = "connected" });
        }
        catch (MySqlException)
        {
            return StatusCode(503, new { status = "unhealthy", service = "backend-csharp", database = "disconnected" });
        }
    }
}
