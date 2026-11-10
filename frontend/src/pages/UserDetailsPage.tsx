import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getUsers, saveUsers } from "../data/users";
import { getReservations, OPEN_STATUSES } from "../data/reservations";

export default function UserDetailsPage() {
  const { id } = useParams(); // the :id of the URL, ex: /users/3 => "3"
  const navigate = useNavigate();
  const [error, setError] = useState("");

  // TODO : GET http://localhost:8000/users/{id} and GET http://localhost:8000/users/{id}/reservations
  const user = getUsers().find((u) => u.id === Number(id));
  const rentals = getReservations().filter((r) => r.userId === Number(id));

  if (!user) {
    return (
      <>
        <h1>User not found</h1>
        <Link to="/users" className="btn">Back to users</Link>
      </>
    );
  }

  const handleRemove = () => {
    // A user with open orders (booked, rented or waiting for the invoice) cannot be removed
    const openOrders = rentals.filter((r) => OPEN_STATUSES.includes(r.status));
    if (openOrders.length > 0) {
      setError(`${user.name} ${user.lastName} has ${openOrders.length} open order(s) and cannot be removed.`);
      return;
    }
    if (!window.confirm(`Remove the user ${user.name} ${user.lastName}?`)) return;
    // TODO : DELETE http://localhost:8000/users/{id}
    saveUsers(getUsers().filter((u) => u.id !== user.id));
    navigate("/users");
  };

  return (
    <>
      <div className="page-header">
        <h1>{user.name} {user.lastName}</h1>
        <div className="row-actions">
          <Link to="/users" className="btn">Back to users</Link>
          <button className="btn danger" onClick={handleRemove}>Remove user</button>
        </div>
      </div>

      {error && <p className="form-error">{error}</p>}

      <dl className="details">
        <dt>Email</dt>
        <dd>{user.email}</dd>
        <dt>Phone</dt>
        <dd>{user.phone}</dd>
        <dt>Role</dt>
        <dd>{user.role}</dd>
      </dl>

      <h2>Rental history</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Order</th>
            <th>Car</th>
            <th>From</th>
            <th>To</th>
            <th>Total</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rentals.length === 0 && (
            <tr>
              <td colSpan={6} className="empty">No rentals yet.</td>
            </tr>
          )}
          {rentals.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.carLabel}</td>
              <td>{r.start}</td>
              <td>{r.end}</td>
              <td>{r.totalPrice.toFixed(2)} €</td>
              <td>
                <span className={OPEN_STATUSES.includes(r.status) ? "badge warn" : "badge ok"}>{r.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
