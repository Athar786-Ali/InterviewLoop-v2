import { Navigate, Outlet, useLocation } from "react-router-dom";

import { isAuthenticated } from "../auth/authStore";

export function ProtectedRoute() {
  const location = useLocation();

  if (!isAuthenticated()) {
    return <Navigate replace state={{ from: location }} to="/login" />;
  }

  return <Outlet />;
}
