import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shadman Wayit, MSc | Software Engineer",
  description: "Software engineering portfolio of Shadman Wayit, featuring full-stack development, quality engineering, and the AI QA Lab.",
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
