import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileCheck2,
  Languages,
  MapPinned,
  Mic,
  Network,
  ShieldCheck,
  Sparkles,
  Users,
  Workflow,
} from "lucide-react";

import { Logo } from "@/components/brand";
import { Button } from "@/components/ui/button";

const SIGNALS = [
  { icon: Mic, label: "Voice Intake", value: "Hindi + local language" },
  { icon: BrainCircuit, label: "Profile AI", value: "Need, skill, intent" },
  { icon: Sparkles, label: "Skill Match", value: "NSQF mapped" },
  { icon: MapPinned, label: "Livelihood Map", value: "Jaipur district signals" },
];

const METRICS = [
  ["94%", "match confidence"],
  ["12", "demand signals"],
  ["5", "language modes"],
  ["360", "journey tracking"],
];

const FLOW = [
  { icon: Mic, label: "बातचीत / Voice", detail: "Beneficiary interview" },
  { icon: Database, label: "Profile", detail: "Structured livelihood record" },
  { icon: Network, label: "Matching", detail: "Skills, schemes, training" },
  { icon: FileCheck2, label: "Action", detail: "Application and outcome" },
];

const GOVERNANCE = [
  { label: "Admin", value: "User control, audit, district overview" },
  { label: "Officer", value: "Beneficiaries, reports, demand map" },
  { label: "Provider", value: "Training batches, applications, outcomes" },
  { label: "Beneficiary", value: "Voice assistant and personal roadmap" },
];

const INTELLIGENCE = [
  "Mother-tongue interview capture",
  "Eligibility and scheme fit",
  "Skill-gap and NSQF level mapping",
  "Local opportunity ranking",
  "Outcome and placement tracking",
  "Role-based data visibility",
];

function IndiaFlag() {
  return (
    <div className="grid h-10 w-16 overflow-hidden rounded-sm border border-border shadow-sm" aria-label="Indian flag accent">
      <div className="bg-[#FF9933]" />
      <div className="relative bg-white">
        <div className="absolute left-1/2 top-1/2 size-4 -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary" />
      </div>
      <div className="bg-[#138808]" />
    </div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen overflow-hidden bg-background">
      <div className="h-1 w-full gov-stripe" />

      <header className="container relative z-20 flex items-center justify-between py-4">
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
        <section className="container grid min-h-[calc(100vh-76px)] gap-10 pb-14 pt-8 lg:grid-cols-[0.92fr_1.08fr] lg:items-center">
          <div className="max-w-2xl animate-fade-in">
            <div className="flex flex-wrap items-center gap-3">
              <IndiaFlag />
              <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-semibold text-muted-foreground shadow-sm">
                <span className="size-1.5 rounded-full bg-success" />
                SIH26097 · PM-AJAY · Government skilling intelligence
              </div>
            </div>

            <h1 className="mt-6 font-display text-4xl font-bold leading-[1.05] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Kaushal <span className="text-accent">AI</span>
              <span className="mt-3 block text-primary">Voice to livelihood</span>
            </h1>

            <div className="mt-5 grid gap-3 text-sm font-semibold text-muted-foreground sm:grid-cols-2">
              <div className="rounded-md border border-border bg-card px-3 py-2">कौशल से आजीविका</div>
              <div className="rounded-md border border-border bg-card px-3 py-2">AI-assisted PM-AJAY delivery</div>
              <div className="rounded-md border border-border bg-card px-3 py-2">District demand visibility</div>
              <div className="rounded-md border border-border bg-card px-3 py-2">Role-based secure access</div>
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
            <div className="absolute inset-x-8 -top-8 -z-10 h-40 rounded-full bg-primary/10 blur-3xl" />
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

              <div className="grid gap-4 p-4 md:grid-cols-[0.95fr_1.05fr]">
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
                        <div className="h-full rounded-full bg-primary" style={{ width: `${76 + index * 6}%` }} />
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
                        <Workflow className="size-4 text-primary" />
                        Delivery flow
                      </div>
                      <span className="rounded-full bg-success/10 px-2 py-1 text-[10px] font-bold text-success">
                        ACTIVE
                      </span>
                    </div>
                    <div className="space-y-2">
                      {FLOW.map((step, index) => (
                        <div key={step.label} className="relative flex items-center gap-3 rounded-md bg-secondary/60 px-3 py-2">
                          {index < FLOW.length - 1 ? <span className="absolute left-[26px] top-10 h-5 w-px bg-border" /> : null}
                          <span className="grid size-7 shrink-0 place-items-center rounded-md bg-card text-primary">
                            <step.icon className="size-3.5" />
                          </span>
                          <div className="min-w-0">
                            <div className="text-xs font-bold">{step.label}</div>
                            <div className="text-[11px] font-medium text-muted-foreground">{step.detail}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-border bg-card/70">
          <div className="container grid gap-8 py-14 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
                <ShieldCheck className="size-3.5" />
                Ministry-ready architecture
              </div>
              <h2 className="mt-4 font-display text-3xl font-bold tracking-tight">Formal, auditable, multilingual.</h2>
              <div className="mt-5 grid gap-2 text-sm font-semibold text-muted-foreground">
                {INTELLIGENCE.map((item) => (
                  <div key={item} className="flex items-center gap-2">
                    <CheckCircle2 className="size-4 text-success" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-border bg-background p-4 shadow-sm">
              <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                <div className="space-y-3">
                  <div className="rounded-md border border-border bg-card p-3 text-sm font-bold">Beneficiary voice</div>
                  <div className="rounded-md border border-border bg-card p-3 text-sm font-bold">Skill records</div>
                  <div className="rounded-md border border-border bg-card p-3 text-sm font-bold">Local demand</div>
                </div>
                <div className="flex h-full flex-col items-center justify-center gap-3">
                  <span className="h-px w-12 bg-border" />
                  <BrainCircuit className="size-10 rounded-full bg-primary p-2 text-primary-foreground" />
                  <span className="h-px w-12 bg-border" />
                </div>
                <div className="space-y-3">
                  <div className="rounded-md border border-border bg-success/10 p-3 text-sm font-bold text-success">Training pathway</div>
                  <div className="rounded-md border border-border bg-accent/10 p-3 text-sm font-bold">Scheme fit</div>
                  <div className="rounded-md border border-border bg-primary/10 p-3 text-sm font-bold text-primary">Officer dashboard</div>
                </div>
              </div>
              <div className="mt-4 rounded-md border border-dashed border-border bg-secondary/50 p-3 text-center text-xs font-bold text-muted-foreground">
                AI translates field inputs into verified livelihood decisions
              </div>
            </div>
          </div>
        </section>

        <section className="container grid gap-8 py-14 lg:grid-cols-[1.1fr_0.9fr] lg:items-start">
          <div>
            <div className="mb-4 flex items-center gap-2 text-sm font-bold text-primary">
              <Users className="size-4" />
              Access by responsibility
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {GOVERNANCE.map((role) => (
                <div key={role.label} className="rounded-lg border border-border bg-card p-4 shadow-sm">
                  <div className="text-sm font-bold text-foreground">{role.label}</div>
                  <div className="mt-1 text-xs font-semibold text-muted-foreground">{role.value}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between text-xs">
              <span className="font-bold">Livelihood signal map</span>
              <span className="font-semibold text-muted-foreground">Bagru · Jaipur</span>
            </div>
            <div className="relative h-64 overflow-hidden rounded-md bg-secondary">
              <div className="absolute inset-0 bg-[linear-gradient(90deg,hsl(var(--border))_1px,transparent_1px),linear-gradient(0deg,hsl(var(--border))_1px,transparent_1px)] bg-[size:34px_34px] opacity-45" />
              <div className="absolute left-[10%] top-[48%] size-20 rounded-full border-2 border-primary/30 bg-primary/15" />
              <div className="absolute left-[42%] top-[24%] size-24 rounded-full border-2 border-accent/40 bg-accent/20" />
              <div className="absolute right-[10%] top-[50%] size-20 rounded-full border-2 border-success/35 bg-success/15" />
              <div className="absolute left-[18%] top-[55%] h-px w-[64%] bg-primary/35" />
              <MapPinned className="absolute left-[48%] top-[40%] size-8 text-primary" />
              <BarChart3 className="absolute bottom-5 right-5 size-9 rounded-md bg-card p-2 text-success shadow-sm" />
              <Languages className="absolute left-5 top-5 size-9 rounded-md bg-card p-2 text-accent shadow-sm" />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
