import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { getReservations, saveReservations } from "../data/reservations";
import type { Reservation } from "../data/reservations";
import { getUsers } from "../data/users";

// Extra fee rules of the report (Generate PDF invoice)
const AGREED_RETURN_TIME = "10:00"; // TODO : each order will have its own return time
const GRACE_MINUTES = 59; // late return is charged after 59 minutes
const REFUEL_FEE = 40; // €, when the tank is not full
const VAT_RATE = 21; // %, added on top of the subtotal

const DAY_MS = 24 * 60 * 60 * 1000;

// Data written by the employee when the car comes back (ReturnReport in the class diagram)
type ReturnData = {
  date: string;
  time: string;
  km: string;
  fuelFull: boolean;
  damageDescription: string;
  damageFee: string;
};

// One line of the invoice: the rental itself or an extra fee (ExtraFee in the class diagram)
type InvoiceLine = { description: string; quantity: number; unitPrice: number };

// Base price + extra fees. TODO : this calculation will be done by the backend (GenerateInvoiceController)
function calculateLines(r: Reservation, data: ReturnData): InvoiceLine[] {
  const rentalDays = Math.max(1, Math.round((new Date(r.end).getTime() - new Date(r.start).getTime()) / DAY_MS));
  const dailyRate = r.totalPrice / rentalDays;
  const lines: InvoiceLine[] = [
    { description: `Rental (${rentalDays} days)`, quantity: rentalDays, unitPrice: dailyRate },
  ];

  // Late return: one daily rate for each started 24-hour period of delay
  const agreed = new Date(`${r.end}T${AGREED_RETURN_TIME}`);
  const returned = new Date(`${data.date}T${data.time}`);
  const lateMinutes = (returned.getTime() - agreed.getTime()) / 60000;
  if (lateMinutes > GRACE_MINUTES) {
    const lateDays = Math.ceil(lateMinutes / (24 * 60));
    lines.push({ description: "Late return", quantity: lateDays, unitPrice: dailyRate });
  }

  if (!data.fuelFull) {
    lines.push({ description: "Refuel", quantity: 1, unitPrice: REFUEL_FEE });
  }

  const damageFee = Number(data.damageFee);
  if (damageFee > 0) {
    lines.push({ description: `Damage: ${data.damageDescription}`, quantity: 1, unitPrice: damageFee });
  }

  return lines;
}

const euros = (n: number) => `${n.toFixed(2)} €`;

export default function InvoicePage() {
  const { id } = useParams();
  // TODO : GET http://localhost:8000/reservations/{id}
  const reservation = getReservations().find((r) => r.id === Number(id));
  const customer = getUsers().find((u) => u.id === reservation?.userId);

  const [data, setData] = useState<ReturnData>({
    date: reservation?.end ?? "",
    time: AGREED_RETURN_TIME,
    km: "",
    fuelFull: true,
    damageDescription: "",
    damageFee: "0",
  });
  const [step, setStep] = useState<"form" | "preview" | "done">("form");
  const [error, setError] = useState("");

  const set = <K extends keyof ReturnData>(key: K, value: ReturnData[K]) => {
    setData((d) => ({ ...d, [key]: value }));
    setError("");
  };

  if (!reservation) {
    return (
      <>
        <h1>Order not found</h1>
        <Link to="/orders" className="btn">Back to orders</Link>
      </>
    );
  }

  if (step !== "done" && reservation.status !== "Returned") {
    return (
      <>
        <h1>Order #{reservation.id}</h1>
        <p>This order cannot be invoiced: its status is {reservation.status}. Only returned orders can be invoiced.</p>
        <Link to="/orders" className="btn">Back to orders</Link>
      </>
    );
  }

  const lines = calculateLines(reservation, data);
  const subtotal = lines.reduce((sum, l) => sum + l.quantity * l.unitPrice, 0);
  const vat = (subtotal * VAT_RATE) / 100;
  const total = subtotal + vat;

  // Validate return data, then show the preview
  const handleCalculate = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (data.date < reservation.start) {
      setError("The return date cannot be before the start of the rental.");
      return;
    }
    if (Number(data.damageFee) > 0 && !data.damageDescription.trim()) {
      setError("Describe the damage.");
      return;
    }
    setStep("preview");
  };

  const handleConfirm = () => {
    // TODO : POST http://localhost:8000/reservations/{id}/invoice
    // The backend saves the return report, asks the PDF Generation Service for the PDF and saves the invoice.
    // If the PDF service fails, show an error and keep the order "Returned".
    saveReservations(
      getReservations().map((r) => (r.id === reservation.id ? { ...r, status: "Closed" } : r))
    );
    setStep("done");
  };

  return (
    <>
      <div className="page-header">
        <h1>Invoice for order #{reservation.id}</h1>
        <Link to="/orders" className="btn">Back to orders</Link>
      </div>

      <dl className="details">
        <dt>Customer</dt>
        <dd>{customer ? `${customer.name} ${customer.lastName}` : "Unknown customer"}</dd>
        <dt>Car</dt>
        <dd>{reservation.carLabel}</dd>
        <dt>Rental</dt>
        <dd>{reservation.start} → {reservation.end} (return before {AGREED_RETURN_TIME})</dd>
        <dt>Price</dt>
        <dd>{euros(reservation.totalPrice)}</dd>
      </dl>

      {step === "form" && (
        <form className="card" onSubmit={handleCalculate}>
          <h2>Return data</h2>

          <label>
            Return date
            <input type="date" value={data.date} onChange={(e) => set("date", e.target.value)} required />
          </label>

          <label>
            Return time
            <input type="time" value={data.time} onChange={(e) => set("time", e.target.value)} required />
          </label>

          <label>
            Kilometres at return
            <input type="number" min={0} value={data.km} onChange={(e) => set("km", e.target.value)} required />
          </label>

          <label>
            Fuel tank
            <select value={data.fuelFull ? "full" : "notFull"} onChange={(e) => set("fuelFull", e.target.value === "full")}>
              <option value="full">Full</option>
              <option value="notFull">Not full</option>
            </select>
          </label>

          <label>
            Damage (leave empty if none)
            <input value={data.damageDescription} onChange={(e) => set("damageDescription", e.target.value)} />
          </label>

          <label>
            Damage cost (€)
            <input type="number" min={0} step="0.01" value={data.damageFee} onChange={(e) => set("damageFee", e.target.value)} required />
          </label>

          {error && <p className="form-error">{error}</p>}

          <div className="form-actions">
            <button type="submit" className="btn primary">Calculate invoice</button>
          </div>
        </form>
      )}

      {step !== "form" && (
        <>
          <h2>{step === "done" ? `Invoice INV-${reservation.id}` : "Invoice preview"}</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Description</th>
                <th>Quantity</th>
                <th>Unit price</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((l) => (
                <tr key={l.description}>
                  <td>{l.description}</td>
                  <td>{l.quantity}</td>
                  <td className="nowrap">{euros(l.unitPrice)}</td>
                  <td className="nowrap">{euros(l.quantity * l.unitPrice)}</td>
                </tr>
              ))}
              <tr className="subtotal-row">
                <td colSpan={3}>Subtotal</td>
                <td className="nowrap">{euros(subtotal)}</td>
              </tr>
              <tr>
                <td colSpan={3}>VAT {VAT_RATE} %</td>
                <td className="nowrap">{euros(vat)}</td>
              </tr>
              <tr className="total-row">
                <td colSpan={3}>Total</td>
                <td className="nowrap">{euros(total)}</td>
              </tr>
            </tbody>
          </table>

          {step === "preview" && (
            <div className="form-actions invoice-actions">
              <button className="btn" onClick={() => setStep("form")}>Edit return data</button>
              <button className="btn primary" onClick={handleConfirm}>Confirm and generate PDF</button>
            </div>
          )}

          {step === "done" && (
            <p className="success">
              PDF generated: invoice-{reservation.id}.pdf. The order is now closed.
            </p>
          )}
        </>
      )}
    </>
  );
}
