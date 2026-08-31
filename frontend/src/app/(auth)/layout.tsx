import Link from "next/link";

import { Logo } from "@/components/brand";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_1fr]">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-primary p-10 text-primary-foreground lg:flex">
        <div className="absolute inset-0 opacity-[0.13] [background-image:radial-gradient(circle_at_20%_20%,white_1px,transparent_1px)] [background-size:22px_22px]" />
        <Link href="/" className="relative">
          <Logo className="[&_.text-muted-foreground]:text-primary-foreground/70" />
        </Link>
        <div className="relative max-w-md">
          <h2 className="font-display text-3xl font-bold leading-tight">
            A national-scale skilling platform, built for the last mile.
          </h2>
          <p className="mt-4 text-sm text-primary-foreground/80">
            Kaushal AI gives every PM-AJAY beneficiary a voice-first, mother-tongue pathway into
            NSQF-aligned livelihoods — and gives officers the analytics to make it work.
          </p>
          <ul className="mt-6 space-y-2 text-sm text-primary-foreground/90">
            <li>• Voice interviews in 5 languages</li>
            <li>• Explainable recommendation engine</li>
            <li>• District livelihood & skill-gap mapping</li>
            <li>• Outcome tracking to employment</li>
          </ul>
        </div>
        <p className="relative text-xs text-primary-foreground/60">
          Prototype for Smart India Hackathon 2026 · SIH26097
        </p>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
