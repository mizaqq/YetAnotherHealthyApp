import {
  Card,
  CardHeader,
  Button,
  Text,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import { MailRegular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";

const useStyles = makeStyles({
  card: {
    width: "100%",
    maxWidth: "420px",
    ...shorthands.margin("auto"),
    ...shorthands.padding("24px"),
  },
  content: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    ...shorthands.gap("24px"),
    paddingTop: "8px",
  },
  iconContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "80px",
    height: "80px",
    ...shorthands.borderRadius(tokens.borderRadiusCircular),
    backgroundColor: tokens.colorBrandBackground2,
  },
  icon: {
    fontSize: "40px",
    color: tokens.colorBrandForeground1,
  },
  textContainer: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap("12px"),
    textAlign: "center",
  },
  buttonContainer: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap("12px"),
    width: "100%",
    paddingTop: "8px",
  },
});

type EmailConfirmationViewProps = {
  email?: string;
};

export function EmailConfirmationView({
  email,
}: EmailConfirmationViewProps): JSX.Element {
  const styles = useStyles();
  const navigate = useNavigate();

  return (
    <Card className={styles.card}>
      <CardHeader
        header={<Text size={700} weight="bold">Sprawdź swoją skrzynkę pocztową</Text>}
      />
      <div className={styles.content}>
        <div className={styles.iconContainer}>
          <MailRegular className={styles.icon} />
        </div>
        <div className={styles.textContainer}>
          <Text size={400}>
            Wysłaliśmy wiadomość z linkiem aktywacyjnym na adres:
          </Text>
          {email && (
            <Text size={500} weight="semibold">
              {email}
            </Text>
          )}
          <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
            Kliknij w link w wiadomości, aby potwierdzić swoje konto i móc się zalogować.
          </Text>
          <Text size={300} style={{ color: tokens.colorNeutralForeground3 }}>
            Nie widzisz wiadomości? Sprawdź folder spam lub spróbuj zarejestrować się ponownie.
          </Text>
        </div>
        <div className={styles.buttonContainer}>
          <Button
            appearance="primary"
            size="large"
            onClick={() => navigate("/login")}
            style={{ width: "100%" }}
          >
            Przejdź do logowania
          </Button>
          <Button
            appearance="subtle"
            size="medium"
            onClick={() => navigate("/register")}
            style={{ width: "100%" }}
          >
            Zarejestruj się ponownie
          </Button>
        </div>
      </div>
    </Card>
  );
}

