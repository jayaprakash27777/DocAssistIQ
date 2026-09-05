import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home Page", () => {
  it("renders the DocAssistIQ heading", () => {
    render(<Home />);
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toBeInTheDocument();
    expect(heading).toHaveTextContent("DocAssistIQ");
  });

  it("renders the subtitle text", () => {
    render(<Home />);
    expect(
      screen.getByText("Clinical Decision Support Platform")
    ).toBeInTheDocument();
  });

  it("renders the phase indicator", () => {
    render(<Home />);
    expect(
      screen.getByText("Phase 0 — Repository Initialized")
    ).toBeInTheDocument();
  });

  it("uses semantic main element", () => {
    render(<Home />);
    const main = screen.getByRole("main");
    expect(main).toBeInTheDocument();
  });
});
