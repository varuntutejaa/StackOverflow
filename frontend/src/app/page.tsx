import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  FileCheck2,
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

const STATS = [
  { value: "5", label: "language modes" },
  { value: "12", label: "district signals" },
  { value: "4", label: "role views" },
];

const WORKFLOW = [
  { icon: Mic, title: "Voice intake", detail: "Hindi and regional interviews" },
  { icon: Sparkles, title: "AI profiling", detail: "Skills, need, eligibility" },
  { icon: Network, title: "Pathway match", detail: "NSQF course and scheme fit" },
  { icon: FileCheck2, title: "Outcome tracking", detail: "Application to livelihood" },
];

const MODULES = [
  { icon: Languages, label: "बहुभाषी सहायता" },
  { icon: MapPinned, label: "District opportunity map" },
  { icon: BarChart3, label: "PM-AJAY MIS dashboard" },
  { icon: ShieldCheck, label: "Role-based access" },
];

function FlagStrip() {
  return (
    <div className="flex h-1.5 w-28 overflow-hidden rounded-full" aria-label="Indian flag accent">
      <span className="flex-1 bg-[#FF9933]" />
      <span className="flex-1 bg-white" />
      <span className="flex-1 bg-[#138808]" />
    </div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,hsl(var(--background))_0%,hsl(var(--secondary))_100%)]">
      <header className="border-b border-border bg-card/85 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <Logo />
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Sign in</Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/register">Sign up</Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="container">
        <section className="grid min-h-[calc(100vh-64px)] gap-8 py-8 lg:grid-cols-[0.82fr_1.18fr] lg:items-center">
          <div className="max-w-xl">
            <FlagStrip />
            <div className="mt-5 inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-bold text-muted-foreground shadow-sm">
              <ShieldCheck className="size-3.5 text-primary" />
              SIH26097 · PM-AJAY · Government livelihood platform
            </div>

            <h1 className="mt-5 font-display text-4xl font-bold leading-[1.03] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Kaushal <span className="text-accent">AI</span>
              <span className="block text-primary">for skilling decisions</span>
            </h1>

            <div className="mt-5 max-w-lg text-base font-semibold leading-7 text-muted-foreground">
              Voice-led beneficiary intake, NSQF pathway matching, district demand intelligence, and secure role-based workflows in one formal MIS.
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/login">
                  Sign in <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/register">Sign up</Link>
              </Button>
            </div>

            <div className="mt-8 grid max-w-md grid-cols-3 gap-3">
              {STATS.map((stat) => (
                <div key={stat.label} className="rounded-md border border-border bg-card p-3 shadow-sm">
                  <div className="font-display text-2xl font-bold text-primary">{stat.value}</div>
                  <div className="mt-1 text-[11px] font-bold leading-tight text-muted-foreground">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <div>
                <div className="text-sm font-bold">Officer Command Centre</div>
                <div className="text-xs font-semibold text-muted-foreground">Jaipur Rural · Bagru cluster</div>
              </div>
              <span className="rounded-full bg-success/10 px-2.5 py-1 text-[10px] font-bold text-success">LIVE DEMO</span>
            </div>

            <div className="grid gap-4 p-5 xl:grid-cols-[1.05fr_0.95fr]">
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-md border border-border bg-background p-3">
                    <div className="text-2xl font-bold text-primary">248</div>
                    <div className="text-[11px] font-bold text-muted-foreground">beneficiaries</div>
                  </div>
                  <div className="rounded-md border border-border bg-background p-3">
                    <div className="text-2xl font-bold text-success">71</div>
                    <div className="text-[11px] font-bold text-muted-foreground">matched</div>
                  </div>
                  <div className="rounded-md border border-border bg-background p-3">
                    <div className="text-2xl font-bold text-accent">18</div>
                    <div className="text-[11px] font-bold text-muted-foreground">providers</div>
                  </div>
                </div>

                <div className="rounded-md border border-border bg-background p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="text-sm font-bold">Decision workflow</div>
                    <div className="text-xs font-bold text-muted-foreground">कौशल से आजीविका</div>
                  </div>
                  <div className="space-y-3">
                    {WORKFLOW.map((item) => (
                      <div key={item.title} className="grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-md bg-card px-3 py-2.5">
                        <span className="grid size-9 place-items-center rounded-md bg-primary/10 text-primary">
                          <item.icon className="size-4" />
                        </span>
                        <div className="min-w-0">
                          <div className="text-sm font-bold">{item.title}</div>
                          <div className="text-xs font-semibold text-muted-foreground">{item.detail}</div>
                        </div>
                        <CheckCircle2 className="size-4 text-success" />
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-md border border-border bg-background p-4">
                  <div className="mb-3 flex items-center justify-between text-xs">
                    <span className="font-bold">Livelihood map</span>
                    <span className="font-semibold text-muted-foreground">Bagru</span>
                  </div>
                  <div className="relative h-52 overflow-hidden rounded-md bg-secondary">
                    <div className="absolute inset-0 bg-[linear-gradient(90deg,hsl(var(--border))_1px,transparent_1px),linear-gradient(0deg,hsl(var(--border))_1px,transparent_1px)] bg-[size:30px_30px] opacity-45" />
                    <div className="absolute left-[14%] top-[50%] size-16 rounded-full border-2 border-primary/25 bg-primary/15" />
                    <div className="absolute left-[45%] top-[24%] size-20 rounded-full border-2 border-accent/40 bg-accent/20" />
                    <div className="absolute right-[11%] top-[52%] size-16 rounded-full border-2 border-success/35 bg-success/15" />
                    <div className="absolute left-[21%] top-[57%] h-px w-[58%] bg-primary/35" />
                    <MapPinned className="absolute left-[49%] top-[39%] size-8 text-primary" />
                    <div className="absolute bottom-3 left-3 rounded-md bg-card px-2.5 py-2 text-[11px] font-bold shadow-sm">
                      Textile · logistics · services
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {MODULES.map((item) => (
                    <div key={item.label} className="rounded-md border border-border bg-background p-3">
                      <item.icon className="size-4 text-primary" />
                      <div className="mt-2 text-xs font-bold leading-snug">{item.label}</div>
                    </div>
                  ))}
                </div>

                <div className="rounded-md border border-border bg-primary px-4 py-3 text-primary-foreground">
                  <div className="flex items-center gap-2 text-sm font-bold">
                    <Users className="size-4" />
                    Admin · Officer · Provider · Beneficiary
                  </div>
                  <div className="mt-1 text-xs font-medium text-primary-foreground/80">Each role sees only the workflow it needs.</div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
