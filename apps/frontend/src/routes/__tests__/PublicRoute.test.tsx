import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PublicRoute } from "../PublicRoute";
import * as authStore from "../../lib/authStore";
import * as useProfileHook from "../../hooks/useProfile";

// Mock the auth store and useProfile hook
vi.mock("../../lib/authStore", () => ({
  useAuthStore: vi.fn(),
}));

vi.mock("../../hooks/useProfile", () => ({
  useProfile: vi.fn(),
}));

describe("PublicRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render children when unauthenticated", () => {
    vi.mocked(authStore.useAuthStore).mockReturnValue({
      status: "unauthenticated",
      session: null,
      user: null,
      isAuthenticated: false,
      isRecovery: false,
    });

    vi.mocked(useProfileHook.useProfile).mockReturnValue({
      profile: null,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <div>Login Page</div>
              </PublicRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  it("should redirect to / when authenticated with completed profile", async () => {
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

    vi.mocked(useProfileHook.useProfile).mockReturnValue({
      profile: {
        id: "user-123",
        email: "test@example.com",
        daily_calorie_goal: 2000,
        onboarding_completed_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <div>Login Page</div>
              </PublicRoute>
            }
          />
          <Route path="/" element={<div>Dashboard</div>} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
    
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });

  it("should render children when authenticated but profile loading", () => {
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

    vi.mocked(useProfileHook.useProfile).mockReturnValue({
      profile: null,
      loading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <div>Login Page</div>
              </PublicRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    // Should render nothing while loading
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });

  it("should render children when authenticated but onboarding not completed", () => {
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

    vi.mocked(useProfileHook.useProfile).mockReturnValue({
      profile: {
        id: "user-123",
        email: "test@example.com",
        daily_calorie_goal: null,
        onboarding_completed_at: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <div>Login Page</div>
              </PublicRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    // Should render the public page when onboarding not completed
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });
});

