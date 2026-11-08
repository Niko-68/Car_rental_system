const cars = [
  { id: 1, brand: "Renault", model: "Clio", plate: "AB-123-CD", status: "Available", lastService: "2026-09-12" },
  { id: 2, brand: "Peugeot", model: "208", plate: "EF-456-GH", status: "In maintenance", lastService: "2026-10-28" },
  { id: 3, brand: "Citroën", model: "C3", plate: "IJ-789-KL", status: "Available", lastService: "2026-08-03" },
  { id: 4, brand: "Toyota", model: "Yaris", plate: "MN-012-OP", status: "In maintenance", lastService: "2026-11-01" },
  { id: 5, brand: "Volkswagen", model: "Golf", plate: "QR-345-ST", status: "Available", lastService: "2026-07-19" },
];

export default function Maintenance() {
  return (
    <>
      <h1>Maintenance</h1>
      <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>Brand</th>
            <th>Model</th>
            <th>Plate</th>
            <th>Status</th>
            <th>Last Service</th>
          </tr>
        </thead>
        <tbody>
          {cars.map((car) => (
            <tr key={car.id}>
              <td>{car.id}</td>
              <td>{car.brand}</td>
              <td>{car.model}</td>
              <td>{car.plate}</td>
              <td>
                <span className={car.status === "Available" ? "badge ok" : "badge warn"}>
                  {car.status}
                </span>
              </td>
              <td>{car.lastService}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}