import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shad Wayit | AI QA Lab",
  description: "Explore a guided requirements-to-test workflow with Shad Wayit. Python, Playwright, and AI quality engineering.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
