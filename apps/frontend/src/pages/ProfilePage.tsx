import { useState } from "react";
import {
  Title1,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorState } from "@/components/common/ErrorState";
import { UserProfileCard } from "@/components/profile/UserProfileCard";
import { useProfile } from "@/lib/ProfileProvider";
import { useAuthStore } from "@/lib/authStore";

const useStyles = makeStyles({
  root: {
    minHeight: "100vh",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  container: {
    maxWidth: "1280px",
    ...shorthands.margin("0", "auto"),
    ...shorthands.padding(tokens.spacingVerticalXXL, tokens.spacingHorizontalXXL),
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
});

export default function ProfilePage() {
  const styles = useStyles();
  const { profile, loading, error, updateCalorieGoal, logout } = useProfile();
  const { user } = useAuthStore();
  const [isUpdating, setIsUpdating] = useState(false);

  // Early return: Loading state
  if (loading) {
    return (
      <div className={styles.root}>
        <div className={styles.container}>
          <Title1 as="h1">Profil</Title1>
          <LoadingSpinner message="Ładowanie profilu..." />
        </div>
      </div>
    );
  }

  // Early return: Error state
  if (error) {
    return (
      <div className={styles.root}>
        <div className={styles.container}>
          <Title1 as="h1">Profil</Title1>
          <ErrorState
            message={error}
            onRetry={() => window.location.reload()}
          />
        </div>
      </div>
    );
  }

  // Early return: No profile loaded
  if (!profile) {
    return (
      <div className={styles.root}>
        <div className={styles.container}>
          <Title1 as="h1">Profil</Title1>
          <ErrorState
            message="Nie znaleziono profilu użytkownika"
            onRetry={() => window.location.reload()}
          />
        </div>
      </div>
    );
  }

  // Wrapper for updateCalorieGoal to track updating state
  const handleUpdateGoal = async (newGoal: number): Promise<void> => {
    setIsUpdating(true);
    try {
      await updateCalorieGoal(newGoal);
    } finally {
      setIsUpdating(false);
    }
  };

  // Happy path: Success state with loaded profile
  return (
    <div className={styles.root}>
      <div className={styles.container}>
        <Title1 as="h1">Profil</Title1>
        <UserProfileCard
          profile={profile}
          userEmail={user?.email}
          isUpdating={isUpdating}
          onSaveGoal={handleUpdateGoal}
          onLogout={() => { void logout(); }}
        />
      </div>
    </div>
  );
}


