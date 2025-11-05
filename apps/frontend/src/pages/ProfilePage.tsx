import {
  Title1,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { ErrorState } from "@/components/common/ErrorState";
import { UserProfileCard } from "@/components/profile/UserProfileCard";
import { useProfile } from "@/hooks/useProfile";

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
  const { profile, updateCalorieGoal, logout } = useProfile();

  // Loading state
  if (profile.isLoading) {
    return (
      <div className={styles.root}>
        <div className={styles.container}>
          <Title1 as="h1">Profil</Title1>
          <LoadingSpinner message="Ładowanie profilu..." />
        </div>
      </div>
    );
  }

  // Error state
  if (profile.error) {
    return (
      <div className={styles.root}>
        <div className={styles.container}>
          <Title1 as="h1">Profil</Title1>
          <ErrorState
            message={profile.error}
            onRetry={() => window.location.reload()}
          />
        </div>
      </div>
    );
  }

  // Success state
  return (
    <div className={styles.root}>
      <div className={styles.container}>
        <Title1 as="h1">Profil</Title1>
        <UserProfileCard
          profile={profile}
          onSaveGoal={updateCalorieGoal}
          onLogout={() => { void logout(); }}
        />
      </div>
    </div>
  );
}


