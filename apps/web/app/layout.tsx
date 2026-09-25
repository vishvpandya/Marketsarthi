import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MarketSarthi — Evidence before expansion",
  description: "An evidence-first regional expansion copilot for Indian merchants.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
