/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Error Boundary.
 *
 * Catches render errors in shell child trees and displays a safe
 * recovery panel. No stack traces or internal details are shown to users.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <SomeComponent />
 *   </ErrorBoundary>
 */

"use client";

import React from "react";

interface Props {
  children: React.ReactNode;
  /** Optional custom fallback UI */
  fallback?: React.ReactNode;
}

interface State {
  hasError: boolean;
  errorId: string | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, errorId: null };
  }

  static getDerivedStateFromError(_err: Error): State {
    return {
      hasError: true,
      errorId: `err-${Date.now().toString(36)}`,
    };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Log for correlation — in production this goes to your observability stack.
    console.error("[ErrorBoundary]", {
      errorId: this.state.errorId,
      message: error.message,
      componentStack: info.componentStack,
    });
  }

  handleRetry = () => {
    this.setState({ hasError: false, errorId: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="error-boundary" role="alert" aria-live="assertive">
          <div className="error-boundary-icon" aria-hidden="true">⚠</div>
          <h2 className="error-boundary-title">Something went wrong</h2>
          <p className="error-boundary-text">
            An unexpected error occurred in this section. Your data has not been
            affected. Please try again or contact support if the problem persists.
          </p>
          {this.state.errorId && (
            <p className="error-boundary-code">
              Reference: <code>{this.state.errorId}</code>
            </p>
          )}
          <button
            className="error-boundary-retry"
            onClick={this.handleRetry}
            autoFocus
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
