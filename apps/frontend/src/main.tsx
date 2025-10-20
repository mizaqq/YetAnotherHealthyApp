import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import ProfilePage from "./pages/ProfilePage";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { AuthProvider } from "./lib/AuthProvider";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { AppLayout } from "./components/navigation/AppLayout";
import "./index.css";
import { Toaster } from "sonner";
import { ThemeProvider } from "./lib/ThemeProvider";

function AppWithErrorBoundary() {
  const navigate = useNavigate();

  const handleReset = () => {
    // Navigate to dashboard on error reset
    navigate("/");
  };

  return (
    <ErrorBoundary onReset={handleReset}>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<AppLayout><DashboardPage /></AppLayout>} />
          <Route path="/history" element={<AppLayout><HistoryPage /></AppLayout>} />
          <Route path="/profile" element={<AppLayout><ProfilePage /></AppLayout>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/onboarding" element={<OnboardingPage />} />
        </Routes>
        <Toaster />
      </AuthProvider>
    </ErrorBoundary>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider>
      <App>
        <BrowserRouter>
          <AppWithErrorBoundary />
        </BrowserRouter>
      </App>
    </ThemeProvider>
  </React.StrictMode>,
);


