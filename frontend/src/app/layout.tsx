import type { Metadata } from "next";
import "./globals.css";
import Navigation from "./components/Navigation";

export const metadata: Metadata = {
  title: "ClearBill | Healthcare Made Clear",
  description: "AI-powered healthcare navigator and medical bill dispute assistant.",
  keywords: ["healthcare", "urgent care", "medical costs", "insurance", "AI healthcare", "medical bill dispute"],
  openGraph: {
    title: "ClearBill",
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
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Navigation />
        {children}
      </body>
    </html>
  );
}
