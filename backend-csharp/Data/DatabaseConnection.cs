namespace AgenciaBackend.Data;

public sealed class DatabaseConnection
{
    public DatabaseConnection(IConfiguration configuration)
    {
        ConnectionString = configuration.GetConnectionString("Default")
            ?? throw new InvalidOperationException("No se configuró la cadena de conexión MySQL.");
    }

    public string ConnectionString { get; }
}
