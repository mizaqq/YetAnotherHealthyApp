import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import HistoryPage from "./pages/HistoryPage";
import ProfilePage from "./pages/ProfilePage";
import { LoginPage } from "./pages/auth/LoginPage";
import { RegisterPage } from "./pages/auth/RegisterPage";
import { ResetPasswordRequestPage } from "./pages/auth/ResetPasswordRequestPage";
import { ResetPasswordConfirmPage } from "./pages/auth/ResetPasswordConfirmPage";
import { EmailConfirmationPage } from "./pages/auth/EmailConfirmationPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { AuthProvider } from "./lib/AuthProvider";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { AppLayout } from "./components/navigation/AppLayout";
import { DashboardRefreshProvider } from "./lib/DashboardRefreshContext";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import { PublicRoute } from "./routes/PublicRoute";
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
        <DashboardRefreshProvider>
          <Routes>
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <AppLayout><DashboardPage /></AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/history" 
              element={
                <ProtectedRoute>
                  <AppLayout><HistoryPage /></AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/profile" 
              element={
                <ProtectedRoute>
                  <AppLayout><ProfilePage /></AppLayout>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/onboarding" 
              element={
                <ProtectedRoute>
                  <OnboardingPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              } 
            />
            <Route 
              path="/register" 
              element={
                <PublicRoute>
                  <RegisterPage />
                </PublicRoute>
              } 
            />
            <Route 
              path="/reset-password" 
              element={
                <PublicRoute>
                  <ResetPasswordRequestPage />
                </PublicRoute>
              } 
            />
            <Route 
              path="/reset-password/confirm" 
              element={<ResetPasswordConfirmPage />} 
            />
            <Route 
              path="/email-confirmation" 
              element={
                <PublicRoute>
                  <EmailConfirmationPage />
                </PublicRoute>
              } 
            />
          </Routes>
        </DashboardRefreshProvider>
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


