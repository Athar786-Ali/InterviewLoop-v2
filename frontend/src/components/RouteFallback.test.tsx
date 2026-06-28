import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { NotFoundPage, RouteLoader } from "./RouteFallback";

describe("RouteFallback", () => {
  it("renders the route loader", () => {
    render(<RouteLoader />);

    expect(screen.getByText("Loading workspace")).toBeInTheDocument();
  });

  it("renders the not found recovery link", () => {
    render(
      <MemoryRouter>
        <NotFoundPage />
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Return to dashboard" })).toHaveAttribute("href", "/");
  });
});
