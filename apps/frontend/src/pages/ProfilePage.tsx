import {
  Title1,
  Text,
  Button,
  Card,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { supabase } from "@/lib/supabaseClient";
import { toast } from "sonner";

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
  card: {
    maxWidth: "600px",
    ...shorthands.padding("24px"),
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
});

export default function ProfilePage() {
  const styles = useStyles();

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut();
      toast.success("Wylogowano pomyślnie");
      // AuthProvider will handle the redirect
    } catch (error) {
      toast.error("Błąd podczas wylogowywania");
      console.error("Logout error:", error);
    }
  };

  return (
    <div className={styles.root}>
      <div className={styles.container}>
        <Title1 as="h1">Profil</Title1>
        <Card className={styles.card}>
          <Text size={400}>Widok w przygotowaniu...</Text>
          <Button
            onClick={() => void handleLogout()}
            appearance="outline"
            size="large"
          >
            Wyloguj się
          </Button>
        </Card>
      </div>
    </div>
  );
}


