import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-sans", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Porchlight · Dispatch Board",
  description: "Extreme-weather wellness check-in board for volunteer coordinators.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full bg-amber-50/40 font-sans text-zinc-900">{children}</body>
    </html>
  );
}
