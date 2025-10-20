import { Button } from "@fluentui/react-components";
import { useTheme } from "@/lib/ThemeProvider";
import {
  WeatherSunny24Regular,
  WeatherMoon24Regular,
} from "@fluentui/react-icons";

export function ThemeToggle(): JSX.Element {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      appearance="transparent"
      icon={theme === "light" ? <WeatherMoon24Regular /> : <WeatherSunny24Regular />}
      onClick={toggleTheme}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      data-testid="theme-toggle"
    />
  );
}

