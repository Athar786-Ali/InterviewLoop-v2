import { beforeEach, describe, expect, it, vi } from "vitest";

import { clearTokens, getAccessToken, getRefreshToken, isAuthenticated, setTokens } from "./authStore";

describe("authStore", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("stores and reads token pairs", () => {
    setTokens({ access_token: "access", refresh_token: "refresh" });

    expect(getAccessToken()).toBe("access");
    expect(getRefreshToken()).toBe("refresh");
    expect(isAuthenticated()).toBe(true);
  });

  it("clears tokens and emits auth-change", () => {
    const listener = vi.fn();
    window.addEventListener("interviewloop:auth-change", listener);
    setTokens({ access_token: "access", refresh_token: "refresh" });

    clearTokens();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(isAuthenticated()).toBe(false);
    expect(listener).toHaveBeenCalledTimes(2);
    window.removeEventListener("interviewloop:auth-change", listener);
  });
});
