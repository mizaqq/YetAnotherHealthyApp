import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/lib/authStore";

type ProtectedRouteProps = {
  children: React.ReactNode;
};

/**
 * Route guard for protected pages that require authentication
 * Redirects based on auth status:
 * - unauthenticated → /login
 * - recovery → /reset-password/confirm
 * - authenticated → renders children
 */
export function ProtectedRoute({ children }: ProtectedRouteProps): React.ReactElement {
  const { status } = useAuthStore();

  // If unauthenticated, redirect to login
  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />;
  }

  // If in recovery mode, redirect to password reset confirmation
  if (status === "recovery") {
    return <Navigate to="/reset-password/confirm" replace />;
  }

  // If authenticated, render children
  if (status === "authenticated") {
    return <>{children}</>;
  }

  // While loading, render nothing (AuthProvider shows loading splash)
  return <></>;
}

