import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { useProfile } from "../useProfile";
import * as authStore from "../../lib/authStore";
import * as api from "../../lib/api";

// Mock dependencies
vi.mock("../../lib/authStore", () => ({
  useAuthStore: vi.fn(),
  signOut: vi.fn(),
}));

vi.mock("../../lib/api", () => ({
  getProfile: vi.fn(),
  updateProfile: vi.fn(),
}));

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("useProfile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  it("should not fetch profile when unauthenticated", async () => {
    vi.mocked(authStore.useAuthStore).mockReturnValue({
      status: "unauthenticated",
      session: null,
      user: null,
      isAuthenticated: false,
      isRecovery: false,
    });

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.profile).toBeNull();
    expect(api.getProfile).not.toHaveBeenCalled();
  });

  it("should fetch profile when authenticated", async () => {
    const mockProfile = {
      user_id: "user-123",
      daily_calorie_goal: 2000,
      onboarding_completed_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

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

    vi.mocked(api.getProfile).mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.profile).toEqual(mockProfile);
    expect(api.getProfile).toHaveBeenCalled();
  });

  it("should redirect to /onboarding on 404 error", async () => {
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

    vi.mocked(api.getProfile).mockRejectedValue(new Error("Resource not found. Please complete your profile setup."));

    renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/onboarding", { replace: true });
    });
  });

  it("should sign out and redirect to /login on 401 error", async () => {
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

    vi.mocked(api.getProfile).mockRejectedValue(new Error("Unauthorized. Please log in again."));
    vi.mocked(authStore.signOut).mockResolvedValue();

    renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(authStore.signOut).toHaveBeenCalledWith({ scope: "global" });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  it("should set error state for other errors", async () => {
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

    const networkError = new Error("Network error");
    vi.mocked(api.getProfile).mockRejectedValue(networkError);

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe("Network error");
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("should support manual refetch", async () => {
    const mockProfile = {
      user_id: "user-123",
      daily_calorie_goal: 2000,
      onboarding_completed_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

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

    vi.mocked(api.getProfile).mockResolvedValue(mockProfile);

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(api.getProfile).toHaveBeenCalledTimes(1);

    // Manually refetch
    await act(async () => {
      await result.current.refetch();
    });

    expect(api.getProfile).toHaveBeenCalledTimes(2);
  });

  it("should update calorie goal successfully", async () => {
    const mockProfile = {
      user_id: "user-123",
      daily_calorie_goal: 2000,
      onboarding_completed_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    const updatedProfile = {
      ...mockProfile,
      daily_calorie_goal: 2500,
    };

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

    vi.mocked(api.getProfile).mockResolvedValue(mockProfile);
    vi.mocked(api.updateProfile).mockResolvedValue(updatedProfile);

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.profile?.daily_calorie_goal).toBe(2000);

    // Update calorie goal
    await act(async () => {
      await result.current.updateCalorieGoal(2500);
    });

    expect(api.updateProfile).toHaveBeenCalledWith({ daily_calorie_goal: 2500 });
    expect(result.current.profile?.daily_calorie_goal).toBe(2500);
  });

  it("should throw error when updating calorie goal with no profile", async () => {
    vi.mocked(authStore.useAuthStore).mockReturnValue({
      status: "unauthenticated",
      session: null,
      user: null,
      isAuthenticated: false,
      isRecovery: false,
    });

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await expect(result.current.updateCalorieGoal(2500)).rejects.toThrow(
        "Cannot update profile: not loaded"
      );
    });
  });

  it("should handle logout successfully", async () => {
    const mockProfile = {
      user_id: "user-123",
      daily_calorie_goal: 2000,
      onboarding_completed_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

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

    vi.mocked(api.getProfile).mockResolvedValue(mockProfile);
    vi.mocked(authStore.signOut).mockResolvedValue();

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Logout
    await act(async () => {
      await result.current.logout();
    });

    expect(authStore.signOut).toHaveBeenCalledWith({ scope: "global" });
    expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
  });

  it("should navigate to login even if logout fails", async () => {
    const mockProfile = {
      user_id: "user-123",
      daily_calorie_goal: 2000,
      onboarding_completed_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

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

    vi.mocked(api.getProfile).mockResolvedValue(mockProfile);
    vi.mocked(authStore.signOut).mockRejectedValue(new Error("Logout failed"));

    const { result } = renderHook(() => useProfile(), {
      wrapper: ({ children }) => <MemoryRouter>{children}</MemoryRouter>,
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Logout
    await act(async () => {
      await result.current.logout();
    });

    expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
  });
});

