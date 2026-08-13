import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PreferencesForm } from "./PreferencesForm";
import { mockFetch } from "../../test/fetchMock";
import type { MockResult } from "../../test/fetchMock";

describe("PreferencesForm (alert configuration flow)", () => {
  it("loads preferences and saves updates", async () => {
    const put = vi.fn();
    const router = (url: string, init?: RequestInit): MockResult => {
      if (url.endsWith("/api/preferences") && init?.method === "PUT") {
        put(JSON.parse(String(init.body)));
        return { body: { temperature_unit: "f", wind_unit: "ms", alert_thresholds: {} } };
      }
      if (url.endsWith("/api/preferences")) {
        return { body: { temperature_unit: "c", wind_unit: "ms", alert_thresholds: {} } };
      }
      return { status: 404, body: { detail: "not found" } };
    };
    mockFetch(router);

    render(<PreferencesForm />);

    const tempSelect = (await screen.findByLabelText(
      /temperature unit/i,
    )) as HTMLSelectElement;
    expect(tempSelect.value).toBe("c");

    fireEvent.change(tempSelect, { target: { value: "f" } });
    expect(tempSelect.value).toBe("f");

    fireEvent.click(screen.getByRole("button", { name: /save preferences/i }));

    expect(await screen.findByText(/saved/i)).toBeInTheDocument();
    expect(put).toHaveBeenCalledTimes(1);
    const body = put.mock.calls[0][0] as { temperature_unit: string };
    expect(body.temperature_unit).toBe("f");
    expect(body).toHaveProperty("alert_thresholds");
  });
});
