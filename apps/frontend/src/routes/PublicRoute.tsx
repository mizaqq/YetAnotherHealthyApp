import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/lib/authStore";
import { useProfile } from "@/hooks/useProfile";

type PublicRouteProps = {
  children: React.ReactNode;
};

/**
 * Route guard for public pages (login, register, etc.)
 * If authenticated and profile completed, redirects to dashboard
 * Otherwise renders children
 */
export function PublicRoute({ children }: PublicRouteProps): React.ReactElement {
  const { status, isAuthenticated } = useAuthStore();
  const { profile, loading } = useProfile();

  // If authenticated and profile is loaded
  if (isAuthenticated && status === "authenticated") {
    // Wait for profile to load
    if (loading) {
      return <></>;
    }

    // If profile exists and onboarding completed, redirect to dashboard
    if (profile?.onboarding_completed_at) {
      return <Navigate to="/" replace />;
    }
  }

  // Otherwise, render the public page
  return <>{children}</>;
}

