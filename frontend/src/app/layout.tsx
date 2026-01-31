import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClearBill Advisor | Find the Right Care at the Right Price",
  description: "AI-powered healthcare navigator that analyzes your symptoms and insurance to recommend the best, most affordable care option near you.",
  keywords: ["healthcare", "urgent care", "medical costs", "insurance", "AI healthcare"],
  openGraph: {
    title: "ClearBill Advisor",
    description: "Find the right care at the right price with AI-powered recommendations",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
