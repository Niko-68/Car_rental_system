const cars = [
  { id: 1, brand: "Renault", model: "Clio", plate: "AB-123-CD", status: "Available" },
  { id: 2, brand: "Peugeot", model: "208", plate: "EF-456-GH", status: "in maintenance" },
  { id: 3, brand: "Citroën", model: "C3", plate: "IJ-789-KL", status: "Available" },
  { id: 4, brand: "Toyota", model: "Yaris", plate: "MN-012-OP", status: "in maintenance"},
  { id: 5, brand: "Volkswagen", model: "Golf", plate: "QR-345-ST", status: "Available" },
];

export default function Cars() {
  return (
    <>
      <h1>Cars</h1>
      <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>Brand</th>
            <th>Model</th>
            <th>Plate</th>
            <th>Status</th>
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
              
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}