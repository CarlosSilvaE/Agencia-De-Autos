using AgenciaBackend.Services;
using Microsoft.AspNetCore.Mvc;

namespace AgenciaBackend.Controllers;

[ApiController]
[Route("api/[controller]")]
public class DashboardController(DashboardService service) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> Get([FromQuery] string filter = "total", [FromQuery] DateOnly? date = null) =>
        Ok(await service.GetAsync(filter, date));
}
