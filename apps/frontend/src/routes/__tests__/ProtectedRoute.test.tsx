import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "../ProtectedRoute";
import * as authStore from "../../lib/authStore";

// Mock the auth store
vi.mock("../../lib/authStore", () => ({
  useAuthStore: vi.fn(),
}));

describe("ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should redirect to /login when unauthenticated", () => {
    vi.mocked(authStore.useAuthStore).mockReturnValue({
      status: "unauthenticated",
      session: null,
      user: null,
      isAuthenticated: false,
      isRecovery: false,
    });

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Login Page")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("should redirect to /reset-password/confirm when in recovery mode", () => {
    vi.mocked(authStore.useAuthStore).mockReturnValue({
      status: "recovery",
      session: {
        access_token: "recovery-token",
        refresh_token: "refresh-token",
        expires_in: 3600,
        expires_at: Date.now() / 1000 + 3600,
        token_type: "bearer",
        user: {
          id: "user-123",
          email: "test@example.com",
          app_metadata: {},
          user_metadata: {},
          aud: "authenticated",
          created_at: new Date().toISOString(),
        },
      },
      user: {
        id: "user-123",
        email: "test@example.com",
        app_metadata: {},
        user_metadata: {},
        aud: "authenticated",
        created_at: new Date().toISOString(),
      },
      isAuthenticated: false,
      isRecovery: true,
    });

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/reset-password/confirm" element={<div>Reset Password</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Reset Password")).toBeInTheDocument();
    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });

  it("should render children when authenticated", () => {
    vi.mocked(authStore.useAuthStore).mockReturnValue({
      status: "authenticated",
      session: {
        access_token: "test-token",
        refresh_token: "refresh-token",
        expires_in: 3600,
        expires_at: Date.now() / 1000 + 3600,
        token_type: "bearer",
        user: {
          id: "user-123",
          email: "test@example.com",
          app_metadata: {},
          user_metadata: {},
          aud: "authenticated",
          created_at: new Date().toISOString(),
        },
      },
      user: {
        id: "user-123",
        email: "test@example.com",
        app_metadata: {},
        user_metadata: {},
        aud: "authenticated",
        created_at: new Date().toISOString(),
      },
      isAuthenticated: true,
      isRecovery: false,
    });

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });

  it("should render nothing when loading", () => {
    vi.mocked(authStore.useAuthStore).mockReturnValue({
      status: "loading",
      session: null,
      user: null,
      isAuthenticated: false,
      isRecovery: false,
    });

    render(
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByText("Protected Content")).not.toBeInTheDocument();
  });
});

