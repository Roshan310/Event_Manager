import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "./globals.css";
import { Providers } from "@/components/providers";
export const metadata: Metadata = {
  title: {
    default: "Evently — Good events. Better connections.",
    template: "%s | Evently",
  },
  description:
    "Discover experiences worth sharing. Find your next event, meet your people, and make a little more of your everyday.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
