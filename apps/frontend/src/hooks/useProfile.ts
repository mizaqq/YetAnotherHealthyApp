import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getProfile, updateProfile } from "@/lib/api";
import { supabase } from "@/lib/supabaseClient";
import { toast } from "sonner";
import { type ProfileViewModel } from "@/types";

export function useProfile() {
  const [profile, setProfile] = useState<ProfileViewModel>({
    email: "",
    dailyCalorieGoal: 0,
    isLoading: true,
    isUpdating: false,
    error: null,
  });
  const navigate = useNavigate();

  // Fetch profile data on mount
  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setProfile((prev) => ({ ...prev, isLoading: true, error: null }));
        
        // Get email from Supabase session
        const {
          data: { session },
        } = await supabase.auth.getSession();
        
        if (!session?.user?.email) {
          throw new Error("No authenticated user found");
        }

        // Get profile data from API
        const profileData = await getProfile();

        setProfile({
          email: session.user.email,
          dailyCalorieGoal: profileData.daily_calorie_goal,
          isLoading: false,
          isUpdating: false,
          error: null,
        });
      } catch (error) {
        const errorMessage =
          error instanceof Error
            ? error.message
            : "Nie udało się załadować profilu. Spróbuj ponownie później.";

        setProfile((prev) => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }));

        // If unauthorized, redirect to login
        if (error instanceof Error && error.message.includes("Unauthorized")) {
          await supabase.auth.signOut();
          navigate("/login", { replace: true });
        }
      }
    };

    void fetchProfile();
  }, [navigate]);

  // Update calorie goal
  const updateCalorieGoal = useCallback(async (newGoal: number) => {
    try {
      setProfile((prev) => ({ ...prev, isUpdating: true, error: null }));

      const updatedProfile = await updateProfile({
        daily_calorie_goal: newGoal,
      });

      setProfile((prev) => ({
        ...prev,
        dailyCalorieGoal: updatedProfile.daily_calorie_goal,
        isUpdating: false,
        error: null,
      }));

      toast.success("Cel kaloryczny został zaktualizowany");
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Błąd zapisu. Sprawdź wartość i spróbuj ponownie.";

      setProfile((prev) => ({
        ...prev,
        isUpdating: false,
        error: errorMessage,
      }));

      toast.error(errorMessage);

      // Re-throw to allow component to handle if needed
      throw error;
    }
  }, []);

  // Logout
  const logout = useCallback(async () => {
    try {
      await supabase.auth.signOut();
      toast.success("Wylogowano pomyślnie");
      navigate("/login", { replace: true });
    } catch (error) {
      toast.error("Błąd podczas wylogowywania");
      console.error("Logout error:", error);
    }
  }, [navigate]);

  return {
    profile,
    updateCalorieGoal,
    logout,
  };
}

