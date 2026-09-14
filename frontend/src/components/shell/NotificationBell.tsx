/* eslint-disable @typescript-eslint/no-unused-vars */
/**
 * DocAssistIQ — Notification Bell.
 *
 * Header icon button for notifications. Placeholder until Phase 9.
 * Shows a badge dot when unread count > 0.
 */

"use client";

interface Props {
  unreadCount?: number;
}

export function NotificationBell({ unreadCount = 0 }: Props) {
  return (
    <button
      className="notif-bell"
      aria-label={
        unreadCount > 0
          ? `${unreadCount} unread notification${unreadCount === 1 ? "" : "s"}`
          : "Notifications — no new notifications"
      }
      aria-haspopup="dialog"
      // No-op: notifications panel coming in Phase 9
      onClick={() => undefined}
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      {unreadCount > 0 && (
        <span className="notif-badge" aria-hidden="true">
          {unreadCount > 9 ? "9+" : unreadCount}
        </span>
      )}
    </button>
  );
}
