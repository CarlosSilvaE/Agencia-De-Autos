namespace AgenciaBackend.Services;

public interface IDashboardStrategy
{
    string Sql { get; }
}

public sealed class TotalDashboardStrategy : IDashboardStrategy
{
    public string Sql => """
        SELECT e.nombre AS estado, COUNT(s.id_servicio) AS cantidad
        FROM estados e LEFT JOIN servicios s ON s.estado=e.nombre
        WHERE e.activo=1 GROUP BY e.nombre ORDER BY e.id_estado
        """;
}

public sealed class DailyDashboardStrategy : IDashboardStrategy
{
    public string Sql => """
        SELECT e.nombre AS estado, COUNT(s.id_servicio) AS cantidad
        FROM estados e LEFT JOIN servicios s ON s.estado=e.nombre AND DATE(s.fecha_ingreso)=@fecha
        WHERE e.activo=1 GROUP BY e.nombre ORDER BY e.id_estado
        """;
}

public sealed class DashboardStrategies
{
    public IDashboardStrategy Create(string filter) =>
        filter.Equals("daily", StringComparison.OrdinalIgnoreCase)
            ? new DailyDashboardStrategy()
            : new TotalDashboardStrategy();
}
