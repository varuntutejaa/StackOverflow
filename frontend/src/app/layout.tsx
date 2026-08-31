import type { Metadata, Viewport } from "next";
import { Inter, Sora } from "next/font/google";

import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const sora = Sora({ subsets: ["latin"], variable: "--font-display", display: "swap" });

export const metadata: Metadata = {
  title: {
    default: "KaushAI — Voice Livelihood Mapping & NSQF Skilling",
    template: "%s · KaushAI",
  },
  description:
    "AI-powered multilingual voice livelihood mapping and NSQF-aligned skilling recommendations for SC communities under PM-AJAY (SIH26097).",
  applicationName: "KaushAI",
};

export const viewport: Viewport = {
  themeColor: "#0B3D91",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${sora.variable}`}>
      <body className="min-h-screen font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
