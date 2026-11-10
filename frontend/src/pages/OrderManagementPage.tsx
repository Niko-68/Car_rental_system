import { useState } from "react";
import { Link } from "react-router-dom";
import { getReservations } from "../data/reservations";
import type { ReservationStatus } from "../data/reservations";
import { getUsers } from "../data/users";

const STATUSES: ReservationStatus[] = ["Confirmed", "Active", "Returned", "Closed", "Cancelled"];

export default function OrderManagementPage() {
  // TODO : GET http://localhost:8000/reservations
  const reservations = getReservations();
  const users = getUsers();
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ReservationStatus | "All">("All");

  // Show the customer's name instead of the id
  const customerName = (userId: number) => {
    const u = users.find((user) => user.id === userId);
    return u ? `${u.name} ${u.lastName}` : "Unknown customer";
  };

  // Keep the orders that match the status filter and the search text (customer or car)
  const text = search.trim().toLowerCase();
  const filteredOrders = reservations.filter(
    (r) =>
      (status === "All" || r.status === status) &&
      (customerName(r.userId).toLowerCase().includes(text) ||
        r.carLabel.toLowerCase().includes(text))
  );

  return (
    <>
      <div className="page-header">
        <h1>Orders</h1>
      </div>

      <div className="filters">
        <input
          className="search"
          type="search"
          placeholder="Search by customer or car"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="select"
          value={status}
          onChange={(e) => setStatus(e.target.value as ReservationStatus | "All")}
        >
          <option value="All">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>Customer</th>
            <th>Car</th>
            <th>Dates</th>
            <th>Total</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredOrders.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{customerName(r.userId)}</td>
              <td>{r.carLabel}</td>
              <td className="nowrap">{r.start}<br />{r.end}</td>
              <td className="nowrap">{r.totalPrice} €</td>
              <td>
                <span className={r.status === "Closed" || r.status === "Cancelled" ? "badge ok" : "badge warn"}>
                  {r.status}
                </span>
              </td>
              <td>
                <div className="row-actions">
                  {/* Only returned orders can be invoiced */}
                  {r.status === "Returned" && (
                    <Link to={`/orders/${r.id}/invoice`} className="btn small primary">Invoice</Link>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {filteredOrders.length === 0 && <p className="empty">No orders match these filters.</p>}
    </>
  );
}
