/* eslint-disable @typescript-eslint/no-unused-vars */
import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import SystemStatus from "@/components/SystemStatus";
import { ThemeProvider } from "@/components/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-sans",
});

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
  display: "swap",
  variable: "--font-heading",
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
    <html lang="en" className={`${inter.variable} ${outfit.variable}`} suppressHydrationWarning>
      <body className="antialiased font-sans bg-[var(--surface-primary)] text-[var(--text-primary)] transition-colors duration-300">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {/* System status bar — shown only when services are degraded or offline */}
          <SystemStatus />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
