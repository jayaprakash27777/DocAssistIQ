import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import SystemStatus from "@/components/SystemStatus";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "DocAssistIQ",
  description:
    "Evidence-grounded Clinical Decision Support for qualified healthcare professionals",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">
        {/* System status bar — shown only when services are degraded or offline */}
        <SystemStatus />
        {children}
      </body>
    </html>
  );
}
