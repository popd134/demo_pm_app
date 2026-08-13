import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatTile } from "./StatTile";

describe("StatTile", () => {
  it("renders label, value and unit", () => {
    render(<StatTile label="Humidity" value="60" unit="%" icon="💧" />);
    expect(screen.getByText("Humidity")).toBeInTheDocument();
    expect(screen.getByText("60")).toBeInTheDocument();
    expect(screen.getByText("%")).toBeInTheDocument();
  });
});
