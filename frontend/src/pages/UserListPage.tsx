import { useState } from "react";
import { Link } from "react-router-dom";
import UserForm from "../components/UserForm";
import { getUsers, saveUsers } from "../data/users";
import type { User, UserFormValues } from "../data/users";

export default function UserListPage() {
  // TODO : GET http://localhost:8000/users
  const [users, setUsers] = useState<User[]>(getUsers);
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null); // null => creating a new user

  // Keep only the users whose name or email contains the text of the search box
  const text = search.trim().toLowerCase();
  const filteredUsers = users.filter(
    (u) =>
      `${u.name} ${u.lastName}`.toLowerCase().includes(text) ||
      u.email.toLowerCase().includes(text)
  );

  // Change the list on the screen and in the shared data at the same time
  const updateUsers = (list: User[]) => {
    setUsers(list);
    saveUsers(list);
  };

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };

  const openEdit = (u: User) => {
    setEditing(u);
    setFormOpen(true);
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditing(null);
  };

  const handleSubmit = (values: UserFormValues) => {
    if (editing) {
      // TODO : PUT http://localhost:8000/users/{id}
      updateUsers(users.map((u) => (u.id === editing.id ? { ...u, ...values } : u)));
    } else {
      // TODO : POST http://localhost:8000/users
      const nextId = users.length ? Math.max(...users.map((u) => u.id)) + 1 : 1;
      updateUsers([...users, { id: nextId, ...values }]);
    }
    closeForm();
  };

  return (
    <>
      <div className="page-header">
        <h1>Users</h1>
        <button className="btn primary" onClick={openCreate}>+ Create user</button>
      </div>

      <input
        className="search"
        type="search"
        placeholder="Search by name or email"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <table className="table">
        <thead>
          <tr>
            <th>#</th>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filteredUsers.length === 0 && (
            <tr>
              <td colSpan={6} className="empty">No users found.</td>
            </tr>
          )}
          {filteredUsers.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.name} {u.lastName}</td>
              <td>{u.email}</td>
              <td>{u.phone}</td>
              <td>{u.role}</td>
              <td>
                <div className="row-actions">
                  <Link to={`/users/${u.id}`} className="btn small">View</Link>
                  <button className="btn small" onClick={() => openEdit(u)}>Edit</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {formOpen && (
        <UserForm
          // key => the form starts again from zero every time it is opened for another user
          key={editing?.id ?? "new"}
          initialValues={
            editing
              ? {
                  name: editing.name,
                  lastName: editing.lastName,
                  email: editing.email,
                  phone: editing.phone,
                  role: editing.role,
                }
              : undefined
          }
          takenEmails={users.filter((u) => u.id !== editing?.id).map((u) => u.email)}
          onSubmit={handleSubmit}
          onCancel={closeForm}
        />
      )}
    </>
  );
}
