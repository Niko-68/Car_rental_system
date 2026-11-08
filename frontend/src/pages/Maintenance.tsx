import { useState } from "react";
import MaintenanceForm from "../components/MaintenanceForm";
import type { MaintenanceFormValues, MaintenanceRecord } from "../components/MaintenanceForm";

const cars = [
  "Renault Clio (AB-123-CD)",
  "Peugeot 208 (EF-456-GH)",
  "Citroën C3 (IJ-789-KL)",
  "Toyota Yaris (MN-012-OP)",
  "Volkswagen Golf (QR-345-ST)",
];

const initialMaintenances: MaintenanceRecord[] = [
  { id: 1, carLabel: cars[0], type: "Oil change", date: "2026-09-12", cost: 89.9, status: "Done", notes: "" },
  { id: 2, carLabel: cars[1], type: "Brakes", date: "2026-10-28", cost: 240, status: "In progress", notes: "Front pads + discs" },
  { id: 3, carLabel: cars[2], type: "Tyres", date: "2026-08-03", cost: 320, status: "Done", notes: "" },
  { id: 4, carLabel: cars[3], type: "Technical inspection", date: "2026-11-01", cost: 75, status: "Planned", notes: "" },
  { id: 5, carLabel: cars[4], type: "Timing belt", date: "2026-07-19", cost: 550, status: "Done", notes: "" },
];

const badgeClass = (status: string) =>
  status === "Done" ? "badge ok" : "badge warn";

export default function Maintenance() {
  const [maintenances, setMaintenances] = useState<MaintenanceRecord[]>(initialMaintenances);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<MaintenanceRecord | null>(null);

  const openAdd = () => {
    setEditing(null);
    setFormOpen(true);
  };

  const openEdit = (m: MaintenanceRecord) => {
    setEditing(m);
    setFormOpen(true);
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditing(null);
  };

  const handleSubmit = (values: MaintenanceFormValues) => {
    if (editing) {
      // TODO : PUT http://localhost:8000/maintenances/{id}
      setMaintenances((list) =>
        list.map((m) => (m.id === editing.id ? { ...m, ...values } : m))
      );
    } else {
      // TODO : POST http://localhost:8000/maintenances
      setMaintenances((list) => {
        const nextId = list.length ? Math.max(...list.map((m) => m.id)) + 1 : 1;
        return [...list, { id: nextId, ...values }];
      });
    }
    closeForm();
  };

  const handleDelete = (m: MaintenanceRecord) => {
    if (!window.confirm(`Delete maintenance "${m.type}" for ${m.carLabel}?`)) return;
    // TODO : DELETE http://localhost:8000/maintenances/{id}
    setMaintenances((list) => list.filter((x) => x.id !== m.id));
  };

  return (
    <>
      <div className="page-header">
        <h1>Maintenance</h1>
        <button className="btn primary" onClick={openAdd}>+ Add maintenance</button>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>Car</th>
            <th>Type</th>
            <th>Date</th>
            <th>Cost</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {maintenances.length === 0 && (
            <tr>
              <td colSpan={7} className="empty">No maintenance yet.</td>
            </tr>
          )}
          {maintenances.map((m) => (
            <tr key={m.id}>
              <td>{m.id}</td>
              <td>{m.carLabel}</td>
              <td>{m.type}</td>
              <td>{m.date}</td>
              <td>{m.cost.toFixed(2)} €</td>
              <td>
                <span className={badgeClass(m.status)}>{m.status}</span>
              </td>
              <td>
                <div className="row-actions">
                  <button className="btn small" onClick={() => openEdit(m)}>Edit</button>
                  <button className="btn small danger" onClick={() => handleDelete(m)}>Delete</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {formOpen && (
        <MaintenanceForm
          // key => le formulaire est réinitialisé à chaque ouverture / changement de ligne
          key={editing?.id ?? "new"}
          cars={cars}
          initialValues={
            editing
              ? {
                  carLabel: editing.carLabel,
                  type: editing.type,
                  date: editing.date,
                  cost: editing.cost,
                  status: editing.status,
                  notes: editing.notes,
                }
              : undefined
          }
          onSubmit={handleSubmit}
          onCancel={closeForm}
        />
      )}
    </>
  );
}