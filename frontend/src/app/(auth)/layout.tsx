import Link from "next/link";
import { BadgeCheck, MapPinned, ScrollText, Sparkles } from "lucide-react";

import { Logo } from "@/components/brand";
import { GovStripe } from "@/components/marketing";

const HIGHLIGHTS = [
  { icon: Sparkles, text: "Explainable NSQF matching — every point traces to a named factor" },
  { icon: MapPinned, text: "District livelihood mapping and skill-gap analysis" },
  { icon: BadgeCheck, text: "Outcome tracking from interview through to income" },
  { icon: ScrollText, text: "Role-based access with an append-only audit log" },
];

/**
 * Split layout for every authentication screen.
 *
 * The left panel is the credibility half — it carries the tricolour rule, the
 * departmental line and what the platform actually does, so a first-time officer
 * arriving on a bare sign-in URL still knows what they are signing in to. It is
 * hidden below `lg`, where the form deserves the whole viewport.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-primary p-12 text-primary-foreground lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.14] [background-image:radial-gradient(circle_at_1px_1px,white_1px,transparent_0)] [background-size:24px_24px]"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -right-24 -top-24 size-[28rem] rounded-full bg-white/5 blur-3xl"
          aria-hidden
        />

        <Link href="/" className="relative w-fit" aria-label="Kaushal AI home">
          <Logo className="[&_.text-muted-foreground]:text-primary-foreground/70" />
        </Link>

        <div className="relative max-w-md">
          <h2 className="font-display text-4xl font-bold leading-[1.1] tracking-tight">
            A national-scale skilling platform, built for the last mile.
          </h2>
          <p className="mt-5 text-sm leading-7 text-primary-foreground/80">
            Kaushal AI gives every PM-AJAY beneficiary a voice-first pathway into NSQF-aligned
            livelihoods in their own language — and gives officers the evidence to plan against.
          </p>

          <ul className="mt-8 space-y-3.5">
            {HIGHLIGHTS.map((item) => (
              <li key={item.text} className="flex items-start gap-3">
                <span className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-md bg-white/10">
                  <item.icon className="size-3.5" />
                </span>
                <span className="text-sm leading-6 text-primary-foreground/90">{item.text}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="relative">
          <GovStripe className="w-28 rounded-full" />
          <p className="mt-3 text-xs text-primary-foreground/60">
            Government of India · Ministry of Social Justice &amp; Empowerment
            <br />
            Prototype for Smart India Hackathon 2026 · SIH26097
          </p>
        </div>
      </aside>

      <main className="flex flex-col">
        <GovStripe className="lg:hidden" />
        <div className="flex flex-1 items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md">
            <Link href="/" className="mb-8 inline-block lg:hidden" aria-label="Kaushal AI home">
              <Logo />
            </Link>
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
