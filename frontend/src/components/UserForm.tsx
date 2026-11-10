import { useState } from "react";
import type { FormEvent } from "react";
import type { Role, UserFormValues } from "../data/users";

type Props = {
  initialValues?: UserFormValues; // present => edit mode
  takenEmails: string[]; // emails of the other users (an email can only be used once)
  onSubmit: (values: UserFormValues) => void;
  onCancel: () => void;
};

const emptyValues: UserFormValues = {
  name: "",
  lastName: "",
  email: "",
  phone: "",
  role: "Employee",
};

export default function UserForm({ initialValues, takenEmails, onSubmit, onCancel }: Props) {
  const isEdit = Boolean(initialValues);
  const [values, setValues] = useState<UserFormValues>(initialValues ?? emptyValues);
  const [password, setPassword] = useState(""); // only when creating a user
  const [error, setError] = useState("");

  const set = <K extends keyof UserFormValues>(key: K, value: UserFormValues[K]) =>
    setValues((v) => ({ ...v, [key]: value }));

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Validate user data: the browser already checks the required fields and the email format
    const email = values.email.trim().toLowerCase();
    if (takenEmails.some((t) => t.toLowerCase() === email)) {
      setError("There is already a user with this email.");
      return;
    }
    // TODO : the password will be sent to the backend together with the new user
    onSubmit({ ...values, email: values.email.trim() });
  };

  return (
    <div className="modal-backdrop" onClick={onCancel}>
      <form className="card modal" onSubmit={handleSubmit} onClick={(e) => e.stopPropagation()}>
        <h2>{isEdit ? "Edit user" : "Create user"}</h2>

        <label>
          First name
          <input value={values.name} onChange={(e) => set("name", e.target.value)} required />
        </label>

        <label>
          Last name
          <input value={values.lastName} onChange={(e) => set("lastName", e.target.value)} required />
        </label>

        <label>
          Email
          <input
            type="email"
            value={values.email}
            onChange={(e) => {
              set("email", e.target.value);
              setError("");
            }}
            required
          />
        </label>

        <label>
          Phone
          <input type="tel" value={values.phone} onChange={(e) => set("phone", e.target.value)} required />
        </label>

        <label>
          Role
          <select value={values.role} onChange={(e) => set("role", e.target.value as Role)}>
            <option value="Customer">Customer</option>
            <option value="Employee">Employee</option>
            <option value="Admin">Admin</option>
          </select>
        </label>

        {!isEdit && (
          <label>
            Password
            <input
              type="password"
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
        )}

        {error && <p className="form-error">{error}</p>}

        <div className="form-actions">
          <button type="button" className="btn" onClick={onCancel}>Cancel</button>
          <button type="submit" className="btn primary">{isEdit ? "Save" : "Create"}</button>
        </div>
      </form>
    </div>
  );
}
