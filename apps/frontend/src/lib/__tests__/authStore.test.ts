import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { signOut, clearPasswordRecovery } from "../authStore";
import { supabase } from "../supabaseClient";

// Mock the supabase client
vi.mock("../supabaseClient", () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
      onAuthStateChange: vi.fn(),
      signOut: vi.fn(),
      refreshSession: vi.fn(),
    },
  },
}));

describe("authStore", () => {
  beforeEach(() => {
    // Clear session storage
    sessionStorage.clear();
    
    // Mock signOut
    vi.mocked(supabase.auth.signOut).mockResolvedValue({ error: null });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("should export signOut function", () => {
    expect(signOut).toBeDefined();
    expect(typeof signOut).toBe("function");
  });

  it("should export clearPasswordRecovery function", () => {
    expect(clearPasswordRecovery).toBeDefined();
    expect(typeof clearPasswordRecovery).toBe("function");
  });

  it("should sign out with global scope", async () => {
    await signOut({ scope: "global" });
    
    expect(supabase.auth.signOut).toHaveBeenCalledWith({ scope: "global" });
  });

  it("should clear recovery flag on sign out", async () => {
    sessionStorage.setItem("yah:is-password-recovery", "1");
    
    await signOut();
    
    expect(sessionStorage.getItem("yah:is-password-recovery")).toBeNull();
  });

  it("should clear recovery flag with clearPasswordRecovery", () => {
    sessionStorage.setItem("yah:is-password-recovery", "1");
    
    clearPasswordRecovery();
    
    expect(sessionStorage.getItem("yah:is-password-recovery")).toBeNull();
  });
});

