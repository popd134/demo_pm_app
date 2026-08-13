import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LocationBar } from "./LocationBar";
import { LocationsProvider } from "../../context/LocationsContext";
import { LOCATIONS, dashboardRouter } from "../../test/apiRouter";
import { mockFetch } from "../../test/fetchMock";

describe("LocationBar (location switch flow)", () => {
  it("switches the active location when a chip is clicked", async () => {
    // Pre-seed both locations into the compared set so both chips render.
    localStorage.setItem(
      "weather-dashboard-locations",
      JSON.stringify({ activeId: 1, compareIds: [1, 2] }),
    );
    mockFetch(dashboardRouter);

    render(
      <LocationsProvider>
        <LocationBar />
      </LocationsProvider>,
    );

    const beta = await screen.findByRole("button", { name: LOCATIONS[1].name });
    expect(beta).toHaveAttribute("aria-pressed", "false");

    fireEvent.click(beta);

    expect(beta).toHaveAttribute("aria-pressed", "true");
    const alpha = screen.getByRole("button", { name: LOCATIONS[0].name });
    expect(alpha).toHaveAttribute("aria-pressed", "false");
  });
});
