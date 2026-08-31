import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  FileCheck2,
  Languages,
  LockKeyhole,
  MapPinned,
  Mic,
  Network,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { Logo } from "@/components/brand";
import { Button } from "@/components/ui/button";

const KPIS = [
  ["12", "district demand signals"],
  ["5", "language modes"],
  ["94%", "demo match confidence"],
];

const PIPELINE = [
  { icon: Mic, label: "Voice intake", meta: "Hindi + local language" },
  { icon: Sparkles, label: "AI profile", meta: "Skill, need, intent" },
  { icon: Network, label: "NSQF match", meta: "Course + scheme fit" },
  { icon: FileCheck2, label: "Outcome", meta: "Training to livelihood" },
];

const CAPABILITIES = [
  { icon: Languages, title: "भाषा-सक्षम", detail: "Voice-first beneficiary interviews" },
  { icon: MapPinned, title: "District map", detail: "Local demand and opportunity view" },
  { icon: ShieldCheck, title: "Role access", detail: "Admin, officer, provider, beneficiary" },
  { icon: BarChart3, title: "Live MIS", detail: "Applications, training, outcomes" },
];

function FlagMark() {
  return (
    <div className="flex h-8 w-12 overflow-hidden rounded-sm border border-border bg-white shadow-sm" aria-label="India flag accent">
      <span className="flex-1 bg-[#FF9933]" />
      <span className="relative flex-1 bg-white">
        <span className="absolute left-1/2 top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary" />
      </span>
      <span className="flex-1 bg-[#138808]" />
    </div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <div className="h-1 w-full gov-stripe" />

      <header className="container flex h-16 items-center justify-between">
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

      <main className="container pb-8">
        <section className="grid min-h-[calc(100vh-112px)] gap-8 py-6 lg:grid-cols-[0.88fr_1.12fr] lg:items-center">
          <div className="max-w-xl">
            <div className="flex flex-wrap items-center gap-3">
              <FlagMark />
              <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-bold text-muted-foreground shadow-sm">
                <LockKeyhole className="size-3.5 text-primary" />
                SIH26097 · PM-AJAY · Secure government platform
              </div>
            </div>

            <h1 className="mt-6 font-display text-4xl font-bold leading-[1.04] tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              Kaushal <span className="text-accent">AI</span>
              <span className="block text-primary">Livelihood Intelligence</span>
            </h1>

            <div className="mt-5 grid gap-2 text-sm font-semibold text-muted-foreground sm:grid-cols-2">
              <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2">
                <CheckCircle2 className="size-4 text-success" />
                कौशल से आजीविका
              </div>
              <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2">
                <CheckCircle2 className="size-4 text-success" />
                Voice to verified profile
              </div>
              <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2">
                <CheckCircle2 className="size-4 text-success" />
                NSQF pathway matching
              </div>
              <div className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-2">
                <CheckCircle2 className="size-4 text-success" />
                District-level MIS
              </div>
            </div>

            <div className="mt-7 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <Link href="/login">
                  Sign in <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/register">Sign up</Link>
              </Button>
            </div>

            <div className="mt-8 grid max-w-lg grid-cols-3 gap-3">
              {KPIS.map(([value, label]) => (
                <div key={label} className="rounded-lg border border-border bg-card p-3 shadow-sm">
                  <div className="font-display text-2xl font-bold text-primary">{value}</div>
                  <div className="mt-1 text-[11px] font-semibold leading-tight text-muted-foreground">{label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <div className="text-sm font-bold">Officer Command Centre</div>
                <div className="text-xs font-semibold text-muted-foreground">Jaipur Rural · Bagru cluster</div>
              </div>
              <span className="rounded-full bg-success/10 px-2.5 py-1 text-[10px] font-bold text-success">LIVE DEMO</span>
            </div>

            <div className="grid gap-4 p-4 xl:grid-cols-[1fr_0.9fr]">
              <div className="space-y-4">
                <div className="rounded-md border border-border bg-background p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="text-sm font-bold">Beneficiary journey</div>
                    <div className="text-xs font-semibold text-muted-foreground">AI assisted</div>
                  </div>
                  <div className="space-y-3">
                    {PIPELINE.map((step, index) => (
                      <div key={step.label} className="grid grid-cols-[auto_1fr_auto] items-center gap-3">
                        <span className="grid size-9 place-items-center rounded-md bg-primary/10 text-primary">
                          <step.icon className="size-4" />
                        </span>
                        <div className="min-w-0">
                          <div className="text-sm font-bold">{step.label}</div>
                          <div className="text-xs font-semibold text-muted-foreground">{step.meta}</div>
                        </div>
                        <span className="h-px w-8 bg-border" />
                        {index < PIPELINE.length - 1 ? null : null}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  {CAPABILITIES.map((item) => (
                    <div key={item.title} className="rounded-md border border-border bg-background p-3">
                      <item.icon className="size-4 text-primary" />
                      <div className="mt-2 text-xs font-bold">{item.title}</div>
                      <div className="mt-1 text-[11px] font-semibold leading-snug text-muted-foreground">{item.detail}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-md border border-border bg-background p-4">
                  <div className="mb-3 flex items-center justify-between text-xs">
                    <span className="font-bold">Livelihood signal map</span>
                    <span className="font-semibold text-muted-foreground">Bagru</span>
                  </div>
                  <div className="relative h-56 overflow-hidden rounded-md bg-secondary">
                    <div className="absolute inset-0 bg-[linear-gradient(90deg,hsl(var(--border))_1px,transparent_1px),linear-gradient(0deg,hsl(var(--border))_1px,transparent_1px)] bg-[size:32px_32px] opacity-40" />
                    <div className="absolute left-[16%] top-[52%] size-16 rounded-full border-2 border-primary/25 bg-primary/15" />
                    <div className="absolute left-[44%] top-[24%] size-20 rounded-full border-2 border-accent/40 bg-accent/20" />
                    <div className="absolute right-[12%] top-[48%] size-16 rounded-full border-2 border-success/35 bg-success/15" />
                    <div className="absolute left-[22%] top-[58%] h-px w-[58%] bg-primary/35" />
                    <MapPinned className="absolute left-[49%] top-[39%] size-8 text-primary" />
                    <div className="absolute bottom-3 left-3 rounded-md bg-card px-2.5 py-2 text-[11px] font-bold shadow-sm">
                      Textile · logistics · services
                    </div>
                  </div>
                </div>

                <div className="rounded-md border border-border bg-background p-4">
                  <div className="mb-3 flex items-center gap-2 text-sm font-bold">
                    <Users className="size-4 text-primary" />
                    Access model
                  </div>
                  <div className="grid gap-2 text-xs font-semibold text-muted-foreground">
                    <div className="flex items-center justify-between rounded-md bg-secondary/70 px-3 py-2">
                      Admin <span className="text-foreground">Full control</span>
                    </div>
                    <div className="flex items-center justify-between rounded-md bg-secondary/70 px-3 py-2">
                      Officer <span className="text-foreground">District MIS</span>
                    </div>
                    <div className="flex items-center justify-between rounded-md bg-secondary/70 px-3 py-2">
                      Provider <span className="text-foreground">Training workflow</span>
                    </div>
                    <div className="flex items-center justify-between rounded-md bg-secondary/70 px-3 py-2">
                      Beneficiary <span className="text-foreground">Assistant only</span>
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
