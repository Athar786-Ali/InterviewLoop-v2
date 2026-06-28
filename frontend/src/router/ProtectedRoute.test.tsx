import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";

import { setTokens } from "../auth/authStore";
import { ProtectedRoute } from "./ProtectedRoute";

function renderRoute() {
  return render(
    <MemoryRouter initialEntries={["/private"]}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route element={<div>Private workspace</div>} path="/private" />
        </Route>
        <Route element={<div>Login screen</div>} path="/login" />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("redirects unauthenticated users to login", () => {
    renderRoute();

    expect(screen.getByText("Login screen")).toBeInTheDocument();
  });

  it("renders protected content when an access token exists", () => {
    setTokens({ access_token: "access", refresh_token: "refresh" });

    renderRoute();

    expect(screen.getByText("Private workspace")).toBeInTheDocument();
  });
});
