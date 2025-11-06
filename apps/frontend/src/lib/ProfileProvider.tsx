import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getProfile, updateProfile as updateProfileApi } from "@/lib/api";
import { useAuthStore, signOut as signOutFromStore } from "@/lib/authStore";
import type { ProfileDTO } from "@/types";

type ProfileContextType = {
  profile: ProfileDTO | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  updateCalorieGoal: (dailyCalorieGoal: number) => Promise<void>;
  logout: () => Promise<void>;
};

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

/**
 * Global profile provider - fetches and manages user profile data
 * Only fetches when authenticated
 */
export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const { status, isAuthenticated } = useAuthStore();
  const [profile, setProfile] = useState<ProfileDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchProfile = useCallback(async (): Promise<void> => {
    // Only fetch if authenticated
    if (!isAuthenticated || status !== "authenticated") {
      setProfile(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const profileData = await getProfile();
      setProfile(profileData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      console.error("Failed to fetch profile:", errorMessage);

      // Handle 404 - profile not found, redirect to onboarding
      const isNotFoundError =
        errorMessage.toLowerCase().includes("not found") ||
        errorMessage.toLowerCase().includes("404");

      if (isNotFoundError) {
        console.log("Profile not found, redirecting to onboarding");
        navigate("/onboarding", { replace: true });
        return;
      }

      // Handle 401 - unauthorized, sign out and redirect to login
      const isUnauthorizedError =
        errorMessage.toLowerCase().includes("unauthorized") ||
        errorMessage.toLowerCase().includes("401");

      if (isUnauthorizedError) {
        console.log("Unauthorized, signing out");
        await signOutFromStore({ scope: "global" });
        navigate("/login", { replace: true });
        return;
      }

      // For other errors, set error state
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, status, navigate]);

  const updateCalorieGoal = useCallback(async (dailyCalorieGoal: number): Promise<void> => {
    if (!profile) {
      throw new Error("Cannot update profile: not loaded");
    }

    try {
      const updatedProfile = await updateProfileApi({ daily_calorie_goal: dailyCalorieGoal });
      setProfile(updatedProfile);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to update calorie goal";
      console.error("Failed to update calorie goal:", errorMessage);
      throw err;
    }
  }, [profile]);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await signOutFromStore({ scope: "global" });
      navigate("/login", { replace: true });
    } catch (err) {
      console.error("Logout failed:", err);
      // Still navigate to login even if logout fails
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  // Fetch profile when authentication status changes
  useEffect(() => {
    void fetchProfile();
  }, [fetchProfile]);

  return (
    <ProfileContext.Provider
      value={{
        profile,
        loading,
        error,
        refetch: fetchProfile,
        updateCalorieGoal,
        logout,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile(): ProfileContextType {
  const context = useContext(ProfileContext);
  if (context === undefined) {
    throw new Error("useProfile must be used within a ProfileProvider");
  }
  return context;
}

