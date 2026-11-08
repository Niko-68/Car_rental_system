import { useState } from "react";
import type { SubmitEvent } from "react";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
  e.preventDefault();
  // TODO : call API FastAPI (POST http://localhost:8000/login)
  navigate("/welcome");
};

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h1>Connexion</h1>
      <label>
        Email
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label>
        Mot de passe
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      <button type="submit" className="btn primary">Connect</button>
    </form>
  );
}