import type { Metadata } from "next";
import { Nav } from "@/components/Nav";
import "@/app/globals.css";

export const metadata: Metadata = {
  title: "SentinelOps AI",
  description: "Security-first DevOps monitoring and repair platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full">
        <Nav />
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">{children}</main>
      </body>
    </html>
  );
}
