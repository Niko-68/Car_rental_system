import { Link, Outlet } from "react-router-dom";
import Dropdown from "./Dropdown";

export default function PublicLayout() {
  return (
    <>
      <header className="header">
        <Link to="/" className="logo">Car Rental</Link>
        <Dropdown
          label="Menu"
          items={[
            { label: "Login", to: "/login" },
            { label: "Description", to: "/description" },
            { label: "Rules", to: "/rules" },
          ]}
        />
      </header>
      <main className="main">
        <Outlet />
      </main>
    </>
  );
}