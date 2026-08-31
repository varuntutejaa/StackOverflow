import Link from "next/link";
import { ArrowRight, BarChart3, Languages, MapPinned, Mic, ShieldCheck, Sparkles } from "lucide-react";

import { Logo } from "@/components/brand";
import { Button } from "@/components/ui/button";

const FEATURES = [
  { icon: Mic, title: "Voice-first intake", body: "Beneficiaries speak in their own language — Hindi, Santhali, Ho, Mundari or English. No forms, no literacy barrier." },
  { icon: Languages, title: "Multilingual NLU", body: "Speech → text → translation → structured profile through a pluggable provider layer (mock, Bhashini, OpenAI)." },
  { icon: Sparkles, title: "Explainable matching", body: "A transparent NSQF-aligned scoring engine — every match score is attributable to named factors, not a black box." },
  { icon: MapPinned, title: "Livelihood mapping", body: "District-level demand, supply and skill-gap intelligence to target PM-AJAY training investment." },
  { icon: BarChart3, title: "Outcome tracking", body: "Interview → recommendation → training → certification → employment, measured end to end." },
  { icon: ShieldCheck, title: "Built for government", body: "RBAC, audit logs, row-level security, and demo/simulated data clearly labelled." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <div className="h-1 w-full gov-stripe" />
      <header className="container flex items-center justify-between py-4">
        <Logo />
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/register">Create account</Link>
          </Button>
        </div>
      </header>

      <main className="container">
        <section className="grid gap-10 py-14 lg:grid-cols-2 lg:items-center lg:py-20">
          <div className="animate-fade-in">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <span className="size-1.5 rounded-full bg-accent" />
              Smart India Hackathon 2026 · Problem SIH26097
            </span>
            <h1 className="mt-5 font-display text-4xl font-bold leading-[1.1] tracking-tight md:text-5xl">
              AI voice livelihood mapping & NSQF skilling for{" "}
              <span className="text-primary">SC communities</span> under PM-AJAY
            </h1>
            <p className="mt-4 max-w-xl text-base text-muted-foreground">
              KaushAI interviews beneficiaries by voice in their mother tongue, builds a structured
              livelihood profile, and recommends explainable, demand-matched NSQF skill pathways —
              then tracks the journey to employment.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/login">
                  Open Admin Portal <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/app/assistant">Try the Voice Assistant</Link>
              </Button>
            </div>
            <p className="mt-4 text-xs text-muted-foreground">
              Demo logins on the sign-in page · all seeded data is clearly labelled DEMO/SIMULATED
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {FEATURES.map((f) => (
              <div key={f.title} className="card-surface p-5">
                <f.icon className="size-5 text-primary" />
                <p className="mt-3 font-display text-sm font-semibold">{f.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 border-t border-border py-12 sm:grid-cols-3">
          {[
            ["5", "Languages supported", "Hindi · Santhali · Ho · Mundari · English"],
            ["10", "NSQF levels modelled", "Skills, job roles, QP alignment & eligibility"],
            ["End-to-end", "Outcome pipeline", "From first interview to verified employment"],
          ].map(([big, label, sub]) => (
            <div key={label}>
              <div className="font-display text-3xl font-bold text-primary">{big}</div>
              <div className="mt-1 text-sm font-medium">{label}</div>
              <div className="text-sm text-muted-foreground">{sub}</div>
            </div>
          ))}
        </section>
      </main>

      <footer className="border-t border-border py-6">
        <div className="container flex flex-col items-center justify-between gap-2 text-xs text-muted-foreground sm:flex-row">
          <span>KaushAI · A prototype for PM-AJAY livelihood & skilling — not an official Government of India system.</span>
          <span>Built for SIH 2026</span>
        </div>
      </footer>
    </div>
  );
}
