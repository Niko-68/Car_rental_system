import { useState } from "react";
import type { FormEvent } from "react";

export type MaintenanceStatus = "Planned" | "In progress" | "Done";

export type MaintenanceRecord = {
  id: number;
  carLabel: string; // ex: "Renault Clio (AB-123-CD)"
  type: string;
  date: string; // YYYY-MM-DD
  cost: number;
  status: MaintenanceStatus;
  notes: string;
};

export type MaintenanceFormValues = Omit<MaintenanceRecord, "id">;

type Props = {
  cars: string[];
  initialValues?: MaintenanceFormValues; // présent => mode modification
  onSubmit: (values: MaintenanceFormValues) => void;
  onCancel: () => void;
};

const emptyValues = (cars: string[]): MaintenanceFormValues => ({
  carLabel: cars[0] ?? "",
  type: "",
  date: new Date().toISOString().slice(0, 10),
  cost: 0,
  status: "Planned",
  notes: "",
});

export default function MaintenanceForm({ cars, initialValues, onSubmit, onCancel }: Props) {
  const isEdit = Boolean(initialValues);
  const [values, setValues] = useState<MaintenanceFormValues>(
    initialValues ?? emptyValues(cars)
  );

  const set = <K extends keyof MaintenanceFormValues>(key: K, value: MaintenanceFormValues[K]) =>
    setValues((v) => ({ ...v, [key]: value }));

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(values);
  };

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <form
        className="card modal"
        onSubmit={handleSubmit}
        onClick={(e) => e.stopPropagation()}
      >
        <h2>{isEdit ? "Edit maintenance" : "Add maintenance"}</h2>

        <label>
          Car
          <select value={values.carLabel} onChange={(e) => set("carLabel", e.target.value)} required>
            {cars.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>

        <label>
          Type
          <input
            type="text"
            placeholder="Oil change, brakes, tyres..."
            value={values.type}
            onChange={(e) => set("type", e.target.value)}
            required
          />
        </label>

        <label>
          Date
          <input
            type="date"
            value={values.date}
            onChange={(e) => set("date", e.target.value)}
            required
          />
        </label>

        <label>
          Cost (€)
          <input
            type="number"
            min={0}
            step="0.01"
            value={values.cost}
            onChange={(e) => set("cost", Number(e.target.value))}
            required
          />
        </label>

        <label>
          Status
          <select
            value={values.status}
            onChange={(e) => set("status", e.target.value as MaintenanceStatus)}
          >
            <option value="Planned">Planned</option>
            <option value="In progress">In progress</option>
            <option value="Done">Done</option>
          </select>
        </label>

        <label>
          Notes
          <textarea
            rows={3}
            value={values.notes}
            onChange={(e) => set("notes", e.target.value)}
          />
        </label>

        <div className="form-actions">
          <button type="button" className="btn" onClick={onCancel}>Cancel</button>
          <button type="submit" className="btn primary">{isEdit ? "Save" : "Add"}</button>
        </div>
      </form>
    </div>
  );
}