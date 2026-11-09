namespace AgenciaBackend.Models;

public sealed record ClientInput(
    int? Id,
    string Nombre,
    string ApellidoPaterno,
    string? ApellidoMaterno,
    string? Telefono,
    string? Email);

public sealed record VehicleInput(
    int? Id,
    int IdMarca,
    int IdModelo,
    int IdAno,
    string Placas,
    string? Color,
    string? Vin);

public sealed record PartInput(int IdRefaccion, int Cantidad, decimal PrecioUnitario);

public sealed record DeliveryInput(
    string Nombre,
    string? Telefono,
    string? RelacionPropietario,
    string? Observaciones);

public sealed record NextServiceInput(DateOnly FechaProgramada, int? Kilometraje, string? Notas);

public sealed record ServiceInput(
    string? Folio,
    string TipoServicio,
    string Descripcion,
    string Estado,
    decimal Costo,
    ClientInput Cliente,
    VehicleInput Vehiculo,
    DeliveryInput Entrega,
    IReadOnlyList<PartInput>? Refacciones,
    NextServiceInput? ProximoServicio);
