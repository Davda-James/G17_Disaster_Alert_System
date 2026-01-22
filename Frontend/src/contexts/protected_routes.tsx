import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();

  // If there is no token, kick them out to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // If token exists, show the protected page (Dashboard)
  return <>{children}</>;
}