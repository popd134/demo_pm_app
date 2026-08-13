import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";
import { ThemeProvider } from "./design/ThemeProvider";
import { dashboardRouter } from "./test/apiRouter";
import { mockFetch } from "./test/fetchMock";

// main.tsx wraps App in ThemeProvider; mirror that for the tests.
function renderApp() {
  return render(
    <ThemeProvider>
      <App />
    </ThemeProvider>,
  );
}

describe("App (E2E-style flows)", () => {
  it("loads the dashboard and shows current conditions", async () => {
    mockFetch(dashboardRouter);
    renderApp();
    // Current-conditions widget renders the first location's temperature.
    expect(await screen.findByText("18°C")).toBeInTheDocument();
  });

  it("navigates to Settings and shows the sign-in gate", async () => {
    mockFetch(dashboardRouter);
    renderApp();
    await screen.findByText("18°C");

    fireEvent.click(screen.getByText("Settings"));

    // Anonymous users see the login form (gate to alert configuration).
    expect(await screen.findByLabelText(/email/i)).toBeInTheDocument();
  });
});
