import React from "react";
import {
  FluentProvider,
  webDarkTheme,
  webLightTheme,
} from "@fluentui/react-components";
import { useTheme } from "@/lib/ThemeProvider";

export function App({ children }: { children: React.ReactNode }) {
  const { theme } = useTheme();
  const currentTheme = theme === "dark" ? webDarkTheme : webLightTheme;

  return (
    <FluentProvider theme={currentTheme}>
      <div
        style={{
          minHeight: "100vh",
          backgroundColor: currentTheme.colorNeutralBackground1,
          color: currentTheme.colorNeutralForeground1,
        }}
      >
        {children}
      </div>
    </FluentProvider>
  );
}


