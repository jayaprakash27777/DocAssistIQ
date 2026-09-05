/**
 * Tests for the SystemStatus component.
 *
 * Verifies all four state transitions:
 *   connecting → operational, degraded, offline
 *
 * All API calls are mocked; no real network requests.
 */

import {
  act,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import SystemStatus from "@/components/SystemStatus";
import * as api from "@/lib/api";

// ── Mock the API module ──────────────────────────────────────
jest.mock("@/lib/api");
const mockGetHealth = api.getHealth as jest.MockedFunction<typeof api.getHealth>;
const mockGetReady = api.getReady as jest.MockedFunction<typeof api.getReady>;

// Suppress console.error noise from React during tests
beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

// ── Helper responses ─────────────────────────────────────────
const healthyHealth = (): Promise<api.ApiResult<api.HealthResponse>> =>
  Promise.resolve({ ok: true, data: { status: "healthy", service: "DocAssistIQ" }, statusCode: 200 });

const healthyReady = (): Promise<api.ApiResult<api.ReadinessResponse>> =>
  Promise.resolve({
    ok: true,
    statusCode: 200,
    data: {
      status: "healthy",
      dependencies: {
        database: { status: "healthy" },
        redis: { status: "healthy" },
        storage: { status: "healthy" },
      },
    },
  });

const degradedReady = (unhealthyDeps: Partial<api.ReadinessResponse["dependencies"]>): Promise<api.ApiResult<api.ReadinessResponse>> =>
  Promise.resolve({
    ok: true,
    statusCode: 503,
    data: {
      status: "degraded",
      dependencies: {
        database: { status: "healthy" },
        redis: { status: "healthy" },
        storage: { status: "healthy" },
        ...unhealthyDeps,
      },
    },
  });

const offlineHealth = (): Promise<api.ApiResult<api.HealthResponse>> =>
  Promise.resolve({ ok: false, error: "Network error", statusCode: 0 });

// ── Tests ────────────────────────────────────────────────────

describe("SystemStatus — Connecting state", () => {
  it("shows connecting message on initial render", async () => {
    // Delay resolution so we can observe the connecting state
    mockGetHealth.mockReturnValue(new Promise(() => {}));
    mockGetReady.mockReturnValue(new Promise(() => {}));

    render(<SystemStatus />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(screen.getByText(/connecting/i)).toBeInTheDocument();
  });
});

describe("SystemStatus — Operational state", () => {
  it("renders nothing when all systems are healthy", async () => {
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady.mockImplementation(healthyReady);

    const { container } = render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
    expect(container.firstChild).toBeNull();
  });
});

describe("SystemStatus — Degraded state", () => {
  it("shows alert when database is unhealthy", async () => {
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady.mockImplementation(() =>
      degradedReady({ database: { status: "unhealthy", error: "ECONNREFUSED" } })
    );

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/degraded/i)).toBeInTheDocument();
    expect(screen.getByText(/database/i)).toBeInTheDocument();
  });

  it("shows alert when redis is unhealthy", async () => {
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady.mockImplementation(() =>
      degradedReady({ redis: { status: "unhealthy", error: "timeout" } })
    );

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/cache/i)).toBeInTheDocument();
  });

  it("shows alert when storage is unhealthy", async () => {
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady.mockImplementation(() =>
      degradedReady({ storage: { status: "unhealthy", error: "bucket not found" } })
    );

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/object storage/i)).toBeInTheDocument();
  });

  it("lists multiple unhealthy dependencies", async () => {
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady.mockImplementation(() =>
      degradedReady({
        database: { status: "unhealthy", error: "down" },
        redis: { status: "unhealthy", error: "down" },
      })
    );

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/database/i)).toBeInTheDocument();
    expect(screen.getByText(/cache/i)).toBeInTheDocument();
  });

  it("shows a dismiss button on degraded state", async () => {
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady.mockImplementation(() =>
      degradedReady({ database: { status: "unhealthy", error: "down" } })
    );

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /dismiss/i })).toBeInTheDocument();
  });

  it("dismisses the banner when dismiss button is clicked", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady.mockImplementation(() =>
      degradedReady({ database: { status: "unhealthy", error: "down" } })
    );

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    const dismissBtn = screen.getByRole("button", { name: /dismiss/i });
    await user.click(dismissBtn);

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("SystemStatus — Offline state", () => {
  it("shows offline alert when health probe fails", async () => {
    mockGetHealth.mockImplementation(offlineHealth);
    mockGetReady.mockImplementation(healthyReady);

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByText(/offline/i)).toBeInTheDocument();
  });

  it("shows the error message in offline state", async () => {
    mockGetHealth.mockImplementation(offlineHealth);
    mockGetReady.mockImplementation(healthyReady);

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it("offline state has no dismiss button (critical alert)", async () => {
    mockGetHealth.mockImplementation(offlineHealth);
    mockGetReady.mockImplementation(healthyReady);

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: /dismiss/i })).not.toBeInTheDocument();
  });
});

describe("SystemStatus — Polling", () => {
  it("re-checks status after 30 seconds", async () => {
    // First call: degraded; second call (after 30s): healthy
    mockGetHealth.mockImplementation(healthyHealth);
    mockGetReady
      .mockImplementationOnce(() =>
        degradedReady({ redis: { status: "unhealthy", error: "down" } })
      )
      .mockImplementation(healthyReady);

    render(<SystemStatus />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });

    // Advance 30 seconds to trigger re-poll
    await act(async () => {
      jest.advanceTimersByTime(30_000);
    });

    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
  });
});
