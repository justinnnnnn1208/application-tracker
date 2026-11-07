import type { Metadata } from "next";
import "./globals.css";
import "@fontsource-variable/inter";

export const metadata: Metadata = { title: "Next step · Application tracker", description: "Your private workspace for graduate job applications." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en-GB"><body>{children}</body></html>;
}
