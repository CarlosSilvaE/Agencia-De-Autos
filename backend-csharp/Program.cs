using AgenciaBackend.Data;
using AgenciaBackend.Services;
using Microsoft.AspNetCore.Identity;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddSingleton<DatabaseConnection>();
builder.Services.AddSingleton<IPasswordHasher<string>, PasswordHasher<string>>();
builder.Services.AddSingleton<DatabaseInitializer>();
builder.Services.AddScoped<DashboardService>();
builder.Services.AddScoped<DashboardStrategies>();

var app = builder.Build();
await app.Services.GetRequiredService<DatabaseInitializer>().InitializeAsync();
app.MapControllers();
app.Run();
