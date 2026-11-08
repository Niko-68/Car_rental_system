import { Link, Outlet, useLocation } from "react-router-dom";
import Dropdown from "./Dropdown";

export default function UserLayout() {
  const { pathname } = useLocation();
  const onProfile = pathname === "/profile";

  return (
    <>
      <header className="header">
        <Link to={onProfile ? "/welcome" : "/profile"} className="btn">
          👤 Profil
        </Link>
        <Dropdown
          label="Menu"
          items={[
            { label: "Cars", to: "/cars" },
            { label: "My rentals", to: "/my-rentals" },
            { label: "Maintenance", to: "/maintenance" },
          ]}
        />
      </header>
      <main className="main">
        <Outlet />
      </main>
    </>
  );
}