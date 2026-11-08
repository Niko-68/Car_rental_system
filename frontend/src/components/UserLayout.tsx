import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import Dropdown from "./Dropdown";

export default function UserLayout() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const onProfile = pathname === "/profile";

  const handleLogout = () => {
    // TODO : delete token / session when we have the login token made (ex: localStorage.removeItem("token"))
    navigate("/");
  };

  return (
    <>
      <header className="header">
        <Link to={onProfile ? "/welcome" : "/profile"} className="btn">
          👤 Profil
        </Link>
        <div className="header-actions">
          <button className="btn" onClick={handleLogout}>Logout</button>
          <Dropdown
            label="Menu"
            items={[
              { label: "Welcome", to: "/welcome" },
              { label: "Cars", to: "/cars" },
              { label: "My rentals", to: "/my-rentals" },
              { label: "Maintenance", to: "/maintenance" },
            ]}
          />
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </>
  );
}