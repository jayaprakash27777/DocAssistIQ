/**
 * DocAssistIQ — Phase 8 Frontend Tests
 *
 * Tests for consultation pages and WsStatus component.
 *
 * Coverage:
 *   NewConsultationPage:
 *     - renders form with textarea and submit button
 *     - shows char counter (initial 0/10000)
 *     - submit disabled when text < 10 chars
 *     - submit enabled when text >= 10 chars
 *     - shows validation error when submitting with short text
 *     - calls createConsultation on valid submit
 *
 *   ConsultationsPage:
 *     - shows loading state initially
 *     - shows empty state when no consultations
 *     - renders list of consultations
 *     - shows "New consultation" button
 *
 *   ConsultationResultPage:
 *     - shows loading initially
 *     - renders placeholder banner
 *     - renders consultation content
 *     - shows not-found panel on error
 *
 *   WsStatus:
 *     - renders with CONNECTING state on mount
 */

import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

// ── Module mocks ─────────────────────────────────────────────

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn() }),
  usePathname: () => "/consultations",
}));

// Mock api functions
jest.mock("@/lib/api", () => ({
  ...jest.requireActual("@/lib/api"),
  createConsultation: jest.fn(),
  getConsultation: jest.fn(),
  listConsultations: jest.fn(),
  getStoredToken: jest.fn(() => null),
  PLACEHOLDER_LABEL: "PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL",
}));

// Mock ToastProvider
jest.mock("@/components/shell/ToastProvider", () => ({
  useToast: () => ({
    toast: {
      success: jest.fn(),
      error: jest.fn(),
      warning: jest.fn(),
    },
  }),
}));

// Mock LoadingSkeleton
jest.mock("@/components/shell/LoadingSkeleton", () => ({
  DashboardSkeleton: () => <div data-testid="dashboard-skeleton" />,
  Skeleton: ({ width, height }: { width?: string; height?: string }) => (
    <div
      data-testid="skeleton"
      style={{ width, height }}
    />
  ),
}));

import * as api from "@/lib/api";

const mockApi = api as jest.Mocked<typeof api>;

// ── Helpers ──────────────────────────────────────────────────

const LABEL = "PLACEHOLDER DEVELOPMENT RESPONSE — NOT CLINICAL";

function mockConsultation(overrides = {}): api.ConsultationResponse {
  return {
    id: "test-id",
    doctor_id: "test-doctor",
    patient_session_id: null,
    input_text: "Patient presents with fever and chills lasting 3 days.",
    status: "completed",
    created_at: "2026-09-06T10:00:00Z",
    updated_at: "2026-09-06T10:00:01Z",
    findings: [],
    ...overrides,
  };
}

function mockSummary(overrides = {}): api.ConsultationSummary {
  return {
    id: "test-uuid-1234",
    status: "completed",
    is_placeholder: true,
    input_preview: "Patient presents with fever and chills…",
    created_at: "2026-09-06T10:00:00Z",
    ...overrides,
  };
}

// ── NewConsultationPage ───────────────────────────────────────

describe("NewConsultationPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  function renderPage() {
    const { default: NewConsultationPage } = require("@/app/(shell)/consultations/new/page");
    return render(<NewConsultationPage />);
  }

  it("renders form with textarea and submit button", () => {
    renderPage();
    expect(screen.getByRole("textbox", { name: /clinical scenario/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /submit consultation/i })).toBeInTheDocument();
  });

  it("shows 0/10000 counter initially", () => {
    renderPage();
    expect(screen.getByText("0 / 10,000")).toBeInTheDocument();
  });

  it("submit button disabled when text is empty", () => {
    renderPage();
    const btn = screen.getByRole("button", { name: /submit consultation/i });
    expect(btn).toBeDisabled();
  });

  it("submit button enabled after entering 10+ chars", async () => {
    const user = userEvent.setup();
    renderPage();
    const textarea = screen.getByRole("textbox", { name: /clinical scenario/i });
    await user.type(textarea, "1234567890"); // exactly 10 chars
    const btn = screen.getByRole("button", { name: /submit consultation/i });
    expect(btn).not.toBeDisabled();
  });

  it("updates char counter as user types", async () => {
    const user = userEvent.setup();
    renderPage();
    const textarea = screen.getByRole("textbox", { name: /clinical scenario/i });
    await user.type(textarea, "Hello");
    expect(screen.getByText("5 / 10,000")).toBeInTheDocument();
  });

  it("shows validation error when submitting with short text", async () => {
    const user = userEvent.setup();
    renderPage();
    const textarea = screen.getByRole("textbox", { name: /clinical scenario/i });
    await user.type(textarea, "short"); // 5 chars, below minimum
    // Button is disabled; directly fire submit on the form
    const form = document.getElementById("new-consultation-form");
    expect(form).toBeInTheDocument();
    if (form) fireEvent.submit(form);
    await waitFor(() => {
      // The error paragraph gets role="alert"
      const alerts = screen.queryAllByRole("alert");
      const hasError = alerts.some((el) =>
        el.textContent?.toLowerCase().includes("character")
      );
      expect(hasError).toBe(true);
    });
  });

  it("shows placeholder safety notice", () => {
    renderPage();
    expect(screen.getByText(LABEL)).toBeInTheDocument();
  });

  it("calls createConsultation on valid submit", async () => {
    mockApi.createConsultation.mockResolvedValue({
      ok: true,
      data: mockConsultation(),
      statusCode: 201,
      requestId: "req-1",
    });

    const user = userEvent.setup();
    renderPage();
    const textarea = screen.getByRole("textbox", { name: /clinical scenario/i });
    await user.type(textarea, "Patient presents with fever and cough for three days.");
    const btn = screen.getByRole("button", { name: /submit consultation/i });
    await user.click(btn);

    await waitFor(() => {
      expect(mockApi.createConsultation).toHaveBeenCalledWith(
        "Patient presents with fever and cough for three days.",
      );
    });
  });
});

// ── ConsultationsPage ────────────────────────────────────────

describe("ConsultationsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  function renderPage() {
    const { default: ConsultationsPage } = require("@/app/(shell)/consultations/page");
    return render(<ConsultationsPage />);
  }

  it("shows skeleton loading state initially", async () => {
    mockApi.listConsultations.mockImplementation(
      () => new Promise(() => {}), // never resolves
    );
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(0);
    });
  });

  it("shows empty state when no consultations", async () => {
    mockApi.listConsultations.mockResolvedValue({
      ok: true,
      data: { items: [], total: 0, page: 1, page_size: 20, pages: 1 },
      statusCode: 200,
      requestId: null,
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/no consultations yet/i)).toBeInTheDocument();
    });
  });

  it("shows consultation list when data is loaded", async () => {
    mockApi.listConsultations.mockResolvedValue({
      ok: true,
      data: {
        items: [mockSummary()],
        total: 1,
        page: 1,
        page_size: 20,
        pages: 1,
      },
      statusCode: 200,
      requestId: null,
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Patient presents with fever and chills…")).toBeInTheDocument();
    });
  });

  it("shows new consultation button", () => {
    mockApi.listConsultations.mockImplementation(() => new Promise(() => {}));
    renderPage();
    expect(screen.getByText(/new consultation/i)).toBeInTheDocument();
  });

  it("shows placeholder safety notice", async () => {
    mockApi.listConsultations.mockResolvedValue({
      ok: true,
      data: { items: [], total: 0, page: 1, page_size: 20, pages: 1 },
      statusCode: 200,
      requestId: null,
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(LABEL)).toBeInTheDocument();
    });
  });
});

// ── ConsultationResultPage ───────────────────────────────────

describe("ConsultationResultPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock React.use to resolve the params promise synchronously
    jest.spyOn(React, "use").mockImplementation((p: unknown) => {
      if (p instanceof Promise) {
        // Return synchronously resolved value for testing
        return { id: "test-uuid-1234" } as never;
      }
      return p as never;
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  function renderPage(id = "test-uuid-1234") {
    const { default: ConsultationResultPage } = require("@/app/(shell)/consultations/[id]/page");
    return render(<ConsultationResultPage params={Promise.resolve({ id })} />);
  }

  it("shows loading skeleton initially", async () => {
    mockApi.getConsultation.mockImplementation(() => new Promise(() => {}));
    renderPage();
    await waitFor(() => {
      expect(screen.getByTestId("dashboard-skeleton")).toBeInTheDocument();
    });
  });

  it("renders placeholder banner", async () => {
    mockApi.getConsultation.mockResolvedValue({
      ok: true,
      data: mockConsultation(),
      statusCode: 200,
      requestId: null,
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByRole("alert", { name: /not a clinical result/i })).toBeInTheDocument();
    });
  });

  it("renders consultation input text", async () => {
    mockApi.getConsultation.mockResolvedValue({
      ok: true,
      data: mockConsultation(),
      statusCode: 200,
      requestId: null,
    });
    renderPage();
    await waitFor(() => {
      expect(
        screen.getByText("Patient presents with fever and chills lasting 3 days."),
      ).toBeInTheDocument();
    });
  });

  it("shows not-found panel on error response", async () => {
    mockApi.getConsultation.mockResolvedValue({
      ok: false,
      error: { code: "CONSULTATION_NOT_FOUND", message: "Not found", statusCode: 404 },
      statusCode: 404,
      requestId: null,
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/consultation not found/i)).toBeInTheDocument();
    });
  });

  it("shows REFERENCE INFORMATION safety footer", async () => {
    mockApi.getConsultation.mockResolvedValue({
      ok: true,
      data: mockConsultation(),
      statusCode: 200,
      requestId: null,
    });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText(/REFERENCE INFORMATION/)).toBeInTheDocument();
    });
  });
});

// ── WsStatus ─────────────────────────────────────────────────

describe("WsStatus", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // WS connect won't work in jsdom — just verify initial render state
    mockApi.getStoredToken.mockReturnValue(null); // no token → UNAVAILABLE path
  });

  it("renders a status pill on mount", () => {
    const { WsStatus } = require("@/components/shell/WsStatus");
    render(<WsStatus />);
    // Should render something — either connecting or unavailable
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows UNAVAILABLE when no token", async () => {
    mockApi.getStoredToken.mockReturnValue(null);
    const { WsStatus } = require("@/components/shell/WsStatus");
    render(<WsStatus />);
    await waitFor(() => {
      expect(screen.getByText("UNAVAILABLE")).toBeInTheDocument();
    });
  });
});
