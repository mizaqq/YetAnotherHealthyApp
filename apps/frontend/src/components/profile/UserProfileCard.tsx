import {
  Card,
  CardHeader,
  Button,
  Label,
  Text,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { SignOutRegular } from "@fluentui/react-icons";
import { EditableField } from "./EditableField";
import { type ProfileDTO } from "@/types";

const useStyles = makeStyles({
  card: {
    maxWidth: "600px",
    ...shorthands.padding("24px"),
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  field: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap("4px"),
  },
  valueText: {
    fontSize: tokens.fontSizeBase400,
    color: tokens.colorNeutralForeground2,
  },
  divider: {
    height: "1px",
    backgroundColor: tokens.colorNeutralStroke2,
    ...shorthands.margin(tokens.spacingVerticalM, "0"),
  },
  footer: {
    display: "flex",
    justifyContent: "flex-start",
    paddingTop: tokens.spacingVerticalS,
  },
});

type UserProfileCardProps = {
  profile: ProfileDTO;
  userEmail: string | undefined;
  isUpdating?: boolean;
  onSaveGoal: (newGoal: number) => Promise<void>;
  onLogout: () => void;
};

export function UserProfileCard({
  profile,
  userEmail,
  isUpdating = false,
  onSaveGoal,
  onLogout,
}: UserProfileCardProps): JSX.Element {
  const styles = useStyles();

  return (
    <Card className={styles.card}>
      <CardHeader
        header={<Text size={600} weight="semibold">Ustawienia profilu</Text>}
        description={<Text size={300}>Zarządzaj swoimi preferencjami i danymi konta</Text>}
      />

      {/* Email field - read only */}
      <div className={styles.field}>
        <Label>Email</Label>
        <Text className={styles.valueText}>{userEmail ?? "Brak adresu email"}</Text>
      </div>

      <div className={styles.divider} role="separator" />

      {/* Editable calorie goal */}
      <EditableField
        label="Dzienny cel kaloryczny"
        initialValue={profile.daily_calorie_goal}
        isUpdating={isUpdating}
        onSave={onSaveGoal}
      />

      <div className={styles.divider} role="separator" />

      {/* Logout button */}
      <div className={styles.footer}>
        <Button
          appearance="outline"
          icon={<SignOutRegular />}
          onClick={onLogout}
          size="large"
          data-testid="profile-logout-button"
        >
          Wyloguj się
        </Button>
      </div>
    </Card>
  );
}

