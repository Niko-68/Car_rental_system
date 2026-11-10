import { Routes, Route } from "react-router-dom";
import PublicLayout from "./components/PublicLayout";
import UserLayout from "./components/UserLayout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Welcome from "./pages/Welcome";
import SimplePage from "./pages/SimplePage";
import Maintenance from "./pages/Maintenance";
import Cars from "./pages/Cars";
import UserListPage from "./pages/UserListPage";
import UserDetailsPage from "./pages/UserDetailsPage";
import OrderManagementPage from "./pages/OrderManagementPage";
import InvoicePage from "./pages/InvoicePage";

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/description" element={<SimplePage title="Description" />} />
        <Route path="/rules" element={<SimplePage title="Rules" />} />
      </Route>

      <Route element={<UserLayout />}>
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/cars" element={<Cars />} />
        <Route path="/my-rentals" element={<SimplePage title="My rentals" />} />
        <Route path="/maintenance" element={<Maintenance />} />
        <Route path="/profile" element={<SimplePage title="My profile" />} />
        <Route path="/users" element={<UserListPage />} />
        <Route path="/users/:id" element={<UserDetailsPage />} />
        <Route path="/orders" element={<OrderManagementPage />} />
        <Route path="/orders/:id/invoice" element={<InvoicePage />} />
      </Route>
    </Routes>
  );
}