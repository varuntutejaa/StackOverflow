import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Languages,
  MapPinned,
  Mic,
  Network,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { Logo } from "@/components/brand";
import { Button } from "@/components/ui/button";

const SIGNALS = [
  { icon: Mic, label: "Voice Intake", value: "5 languages" },
  { icon: BrainCircuit, label: "Profile AI", value: "Structured extraction" },
  { icon: Sparkles, label: "Skill Match", value: "Explainable scoring" },
  { icon: MapPinned, label: "Livelihood Map", value: "Demand vs supply" },
];

const MODULES = [
  "Beneficiary registry",
  "AI interviews",
  "NSQF catalogue",
  "Training workflow",
  "District demand",
  "Outcome tracking",
];

const METRICS = [
  ["94%", "top match confidence"],
  ["12", "district signals"],
  ["5", "supported languages"],
  ["360", "journey visibility"],
];

export default function Landing() {
  return (
    <div className="min-h-screen overflow-hidden bg-background">
      <div className="h-1 w-full gov-stripe" />

      <header className="container relative z-10 flex items-center justify-between py-4">
        <Logo />
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/register">Sign up</Link>
          </Button>
        </div>
      </header>

      <main>
        <section className="container grid min-h-[calc(100vh-76px)] gap-10 pb-10 pt-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div className="max-w-2xl animate-fade-in">
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-semibold text-muted-foreground shadow-sm">
              <span className="size-1.5 rounded-full bg-success" />
              SIH26097 · PM-AJAY · AI livelihood intelligence
            </div>

            <h1 className="mt-5 font-display text-4xl font-bold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Kaush<span className="text-accent">AI</span>
              <span className="mt-3 block text-primary">Voice to livelihood</span>
            </h1>

            <div className="mt-6 grid gap-2 text-sm font-medium text-muted-foreground sm:grid-cols-2">
              <div className="flex items-center gap-2">
                <Languages className="size-4 text-primary" />
                Multilingual beneficiary interviews
              </div>
              <div className="flex items-center gap-2">
                <Network className="size-4 text-primary" />
                NSQF-aligned pathway matching
              </div>
              <div className="flex items-center gap-2">
                <BarChart3 className="size-4 text-primary" />
                District skill-demand intelligence
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 text-primary" />
                Role-based government portal
              </div>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/login">
                  Sign in <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/register">Sign up</Link>
              </Button>
            </div>
          </div>

          <div className="relative">
            <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_40%,hsl(var(--primary)/0.18),transparent_60%)]" />
            <div className="rounded-lg border border-border bg-card shadow-2xl">
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <div className="flex items-center gap-2">
                  <span className="size-2.5 rounded-full bg-destructive" />
                  <span className="size-2.5 rounded-full bg-warning" />
                  <span className="size-2.5 rounded-full bg-success" />
                </div>
                <div className="rounded-full bg-secondary px-3 py-1 text-[11px] font-semibold text-muted-foreground">
                  Live AI dashboard
                </div>
              </div>

              <div className="grid gap-4 p-4 md:grid-cols-[0.9fr_1.1fr]">
                <div className="space-y-3">
                  {SIGNALS.map((item, index) => (
                    <div key={item.label} className="rounded-md border border-border bg-background p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="grid size-8 place-items-center rounded-md bg-primary/10 text-primary">
                            <item.icon className="size-4" />
                          </span>
                          <span className="text-sm font-semibold">{item.label}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">{item.value}</span>
                      </div>
                      <div className="mt-3 h-1.5 rounded-full bg-secondary">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${78 + index * 5}%` }} />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    {METRICS.map(([value, label]) => (
                      <div key={label} className="rounded-md border border-border bg-background p-3">
                        <div className="font-display text-2xl font-bold text-primary">{value}</div>
                        <div className="mt-1 text-xs font-medium text-muted-foreground">{label}</div>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-md border border-border bg-background p-3">
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm font-semibold">
                        <Users className="size-4 text-primary" />
                        Journey modules
                      </div>
                      <span className="rounded-full bg-success/10 px-2 py-1 text-[10px] font-bold text-success">
                        ACTIVE
                      </span>
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {MODULES.map((module) => (
                        <div key={module} className="flex items-center gap-2 rounded-md bg-secondary/60 px-2.5 py-2 text-xs font-medium">
                          <CheckCircle2 className="size-3.5 text-success" />
                          {module}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-md border border-border bg-background p-3">
                    <div className="mb-3 flex items-center justify-between text-xs">
                      <span className="font-semibold">Livelihood signal</span>
                      <span className="text-muted-foreground">Bagru · Jaipur</span>
                    </div>
                    <div className="relative h-28 overflow-hidden rounded-md bg-secondary">
                      <div className="absolute left-[12%] top-[52%] size-16 rounded-full border-2 border-primary/30 bg-primary/15" />
                      <div className="absolute left-[42%] top-[28%] size-20 rounded-full border-2 border-accent/40 bg-accent/20" />
                      <div className="absolute right-[12%] top-[48%] size-14 rounded-full border-2 border-success/35 bg-success/15" />
                      <div className="absolute inset-x-6 top-1/2 h-px bg-border" />
                      <MapPinned className="absolute left-[48%] top-[38%] size-6 text-primary" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
