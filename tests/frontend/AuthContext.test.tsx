/**
 * Frontend Tests - AuthContext
 * Tests the authentication context provider and hooks
 */


// ignore the library import erros, these are due to the structuring of the files in the project. Please refer to the HOW_TO.md file for more details on how to run the tests.


import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { ReactNode } from "react";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("AuthContext", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  // =========================================================================
  // FE-001: Initial State - Not Authenticated
  // =========================================================================
  it("FE-001: should have initial unauthenticated state", async () => {
    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
  });

  // =========================================================================
  // FE-002: Login Success
  // =========================================================================
  it("FE-002: should login successfully with valid credentials", async () => {
    const mockUser = {
      id: "123",
      name: "Test User",
      email: "test@example.com",
      phone: "+919876543210",
      location: { city: "Mumbai", state: "Maharashtra" },
      isAuthorized: false,
      notificationPreferences: { email: true, sms: true, push: true },
      coordinates: { lat: 19.076, lng: 72.877 },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: "jwt-token-123", user: mockUser }),
    });

    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let loginSuccess;
    await act(async () => {
      loginSuccess = await result.current.login("test@example.com", "password");
    });

    expect(loginSuccess).toBe(true);
    expect(localStorageMock.setItem).toHaveBeenCalledWith("token", "jwt-token-123");
  });

  // =========================================================================
  // FE-003: Login Failure - Invalid Credentials
  // =========================================================================
  it("FE-003: should fail login with invalid credentials", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let loginSuccess;
    await act(async () => {
      loginSuccess = await result.current.login("wrong@example.com", "wrongpass");
    });

    expect(loginSuccess).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);
  });

  // =========================================================================
  // FE-004: Signup Success
  // =========================================================================
  it("FE-004: should signup successfully with valid data", async () => {
    const mockUser = {
      id: "456",
      name: "New User",
      email: "new@example.com",
      phone: "+919876543211",
      location: { city: "Delhi", state: "Delhi" },
      isAuthorized: false,
      notificationPreferences: { email: true, sms: true, push: true },
      coordinates: { lat: 28.613, lng: 77.209 },
    };

    // First call is /me (returns 401 since no token initially)
    // Second call is /signup
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ token: "jwt-token-456", user: mockUser }),
    });

    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let signupSuccess;
    await act(async () => {
      signupSuccess = await result.current.signup({
        name: "New User",
        email: "new@example.com",
        phone: "+919876543211",
        city: "Delhi",
        state: "Delhi",
        password: "SecurePass123!",
      });
    });

    expect(signupSuccess).toBe(true);
  });

  // =========================================================================
  // FE-005: Logout
  // =========================================================================
  it("FE-005: should logout and clear token", async () => {
    localStorageMock.getItem.mockReturnValue("existing-token");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        user: {
          id: "789",
          name: "Test",
          email: "test@test.com",
          phone: "+91123",
          location: {},
          isAuthorized: false,
          notificationPreferences: {},
          coordinates: { lat: 0, lng: 0 },
        },
      }),
    });

    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.logout();
    });

    expect(localStorageMock.removeItem).toHaveBeenCalledWith("token");
    expect(result.current.isAuthenticated).toBe(false);
  });

  // =========================================================================
  // FE-006: Token Persistence on Reload
  // =========================================================================
  it("FE-006: should restore session from stored token", async () => {
    const storedUser = {
      id: "stored-123",
      name: "Stored User",
      email: "stored@example.com",
      phone: "+919876543210",
      location: { city: "Mumbai", state: "Maharashtra" },
      isAuthorized: false,
      notificationPreferences: { email: true, sms: true, push: true },
      coordinates: { lat: 19.076, lng: 72.877 },
    };

    localStorageMock.getItem.mockReturnValue("stored-jwt-token");
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ user: storedUser }),
    });

    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    // Initially should be authenticated (token exists)
    expect(result.current.isAuthenticated).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  // =========================================================================
  // FE-007: Invalid Token Handling
  // =========================================================================
  it("FE-007: should clear state when token is invalid", async () => {
    localStorageMock.getItem.mockReturnValue("invalid-token");
    
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(localStorageMock.removeItem).toHaveBeenCalledWith("token");
  });

  // =========================================================================
  // FE-008: Network Error Handling
  // =========================================================================
  it("FE-008: should handle network errors gracefully", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    const { AuthProvider, useAuth } = await import("../../Frontend/src/contexts/AuthContext");

    const wrapper = ({ children }: { children: ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    let loginSuccess;
    await act(async () => {
      loginSuccess = await result.current.login("test@example.com", "password");
    });

    expect(loginSuccess).toBe(false);
  });
});
