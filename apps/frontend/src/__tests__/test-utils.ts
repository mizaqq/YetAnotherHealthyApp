/**
 * Shared test utilities and mock helpers for Vitest tests
 */
import { vi } from 'vitest';
import type { Session } from '@supabase/supabase-js';

/**
 * Mock fetch response helper
 */
export function createMockFetchResponse<T>(
  status: number,
  data?: T,
  statusText = 'OK'
): Response {
  const body = status === 204 ? null : JSON.stringify(data);
  
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    headers: new Headers({ 'Content-Type': 'application/json' }),
    json: () => Promise.resolve(data as T),
    text: () => Promise.resolve(body ?? ''),
    clone: () => createMockFetchResponse(status, data, statusText),
  } as Response;
}

/**
 * Create a mock fetch function that can be configured per-test
 */
export function createMockFetch() {
  return vi.fn<Parameters<typeof fetch>, ReturnType<typeof fetch>>();
}

/**
 * Mock Supabase session for authenticated requests
 */
export function createMockSession(accessToken = 'mock-access-token'): Session {
  return {
    access_token: accessToken,
    refresh_token: 'mock-refresh-token',
    expires_in: 3600,
    expires_at: Date.now() / 1000 + 3600,
    token_type: 'bearer',
    user: {
      id: 'mock-user-id',
      app_metadata: {},
      user_metadata: {},
      aud: 'authenticated',
      created_at: '2025-01-01T00:00:00Z',
    },
  } as Session;
}

/**
 * Mock Supabase auth.getSession() result
 */
export function createMockSupabaseAuth(session: Session | null = createMockSession()) {
  return {
    getSession: vi.fn().mockResolvedValue({
      data: { session },
      error: null,
    }),
  };
}

/**
 * Create a deterministic date for testing
 */
export function setDeterministicDate(isoString = '2025-01-15T12:00:00.000Z') {
  vi.setSystemTime(new Date(isoString));
}

/**
 * Restore real timers after test
 */
export function restoreRealTimers() {
  vi.useRealTimers();
}

/**
 * Mock toast notifications from sonner
 */
export function createMockToast() {
  return {
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  };
}

/**
 * Wait for async operations to complete
 */
export async function waitForAsync() {
  await new Promise((resolve) => setTimeout(resolve, 0));
}

