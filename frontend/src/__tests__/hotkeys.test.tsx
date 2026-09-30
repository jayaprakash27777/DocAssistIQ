import React from "react";
import { render, fireEvent } from "@testing-library/react";
import { useClinicianHotkeys } from "@/hooks/useClinicianHotkeys";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

function TestComponent() {
  useClinicianHotkeys();
  return <div><input data-testid="test-input" /></div>;
}

describe("useClinicianHotkeys", () => {
  beforeEach(() => {
    mockPush.mockClear();
  });

  it("navigates to /consultations/new on Alt+N", () => {
    render(<TestComponent />);
    fireEvent.keyDown(window, { key: "n", altKey: true });
    expect(mockPush).toHaveBeenCalledWith("/consultations/new");
  });

  it("navigates to /dashboard on Alt+D", () => {
    render(<TestComponent />);
    fireEvent.keyDown(window, { key: "d", altKey: true });
    expect(mockPush).toHaveBeenCalledWith("/dashboard");
  });

  it("navigates to /hub on Alt+H", () => {
    render(<TestComponent />);
    fireEvent.keyDown(window, { key: "h", altKey: true });
    expect(mockPush).toHaveBeenCalledWith("/hub");
  });

  it("does not trigger navigation when typing inside input field", () => {
    const { getByTestId } = render(<TestComponent />);
    const input = getByTestId("test-input");
    fireEvent.keyDown(input, { key: "n", altKey: true });
    expect(mockPush).not.toHaveBeenCalled();
  });
});
