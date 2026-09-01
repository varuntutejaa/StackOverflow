import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Building2,
  ClipboardList,
  FileSearch,
  GraduationCap,
  Languages,
  LineChart,
  MapPinned,
  Mic,
  ScrollText,
  ShieldCheck,
  Sparkles,
  UserCog,
  Users,
} from "lucide-react";

import { GovTopBar, Section, SiteFooter, SiteHeader } from "@/components/marketing";
import { Button } from "@/components/ui/button";

/**
 * Public landing page.
 *
 * Written to answer, in order: what is broken today, what this does about it,
 * how the decision is made, and who signs in. An officer evaluating a
 * government MIS wants the mechanism, not adjectives — so the page shows the
 * actual pipeline stages and the real scoring factors rather than claiming to
 * be "AI-powered".
 */

const PROBLEMS = [
  {
    icon: Languages,
    stat: "5 languages",
    title: "The form is the barrier",
    body:
      "PM-AJAY skilling reaches people who may not read the language the paperwork is written in. A form asking them to self-describe their skills excludes the people the scheme exists for.",
  },
  {
    icon: FileSearch,
    stat: "No signal",
    title: "Officers plan without data",
    body:
      "District administrators cannot see who needs which skill, where local demand actually sits, or whether last year's batch led to any income at all.",
  },
  {
    icon: LineChart,
    stat: "Untracked",
    title: "Training ends, the story stops",
    body:
      "Enrolment is recorded; outcomes are not. Without a line from interview to income, there is no way to tell an effective programme from a well-attended one.",
  },
];

const PIPELINE = [
  {
    icon: Mic,
    step: "01",
    title: "Voice intake",
    preview: "Hindi · Santhali · Ho · Mundari · English",
    body:
      "A structured interview in Hindi, Santhali, Ho, Mundari or English. The beneficiary speaks; nobody has to fill anything in.",
  },
  {
    icon: ClipboardList,
    step: "02",
    title: "Structured profile",
    preview: "10th pass · farming · solar interest",
    body:
      "Speech becomes text, text becomes a profile: education, existing skills, interests, mobility and work preference — extracted deterministically, so it can be audited.",
  },
  {
    icon: Sparkles,
    step: "03",
    title: "Explainable match",
    preview: "Solar PV Installer (Suryamitra)",
    body:
      "A transparent weighted score ranks NSQF-aligned trades. Every point traces to a named factor, and the weights are configurable per district.",
  },
  {
    icon: GraduationCap,
    step: "04",
    title: "Training and enrolment",
    preview: "Govt. ITI Ranchi · 12 weeks · fee-free",
    body:
      "Eligibility is checked against the real programme, the application routes to the provider, and seats are tracked against capacity.",
  },
  {
    icon: BadgeCheck,
    step: "05",
    title: "Outcome tracking",
    preview: "Certification → income, before and after",
    body:
      "Certification, placement or self-employment, with income before and after — closing the loop the scheme is measured on.",
  },
];

/** The engine's real factors — see backend/app/services/recommendation_engine.py */
const FACTORS = [
  "Education compatibility",
  "Existing skills",
  "Stated interests",
  "Local demand",
  "Mobility fit",
  "Employment preference",
  "Training availability",
  "Local opportunity",
  "Family synergy",
];

const MODULES = [
  {
    icon: MapPinned,
    title: "District livelihood map",
    body: "Beneficiary distribution, demand versus trained supply, and skill gaps per district.",
  },
  {
    icon: BarChart3,
    title: "Programme analytics",
    body: "Intake, recommendation, enrolment and outcome funnels with income improvement.",
  },
  {
    icon: ScrollText,
    title: "NSQF catalogue",
    body: "Skills, job roles, QP/NCO alignment, eligibility rules, duration and sectors.",
  },
  {
    icon: ShieldCheck,
    title: "Audit and access control",
    body: "Role-based permissions with an append-only audit log of every consequential action.",
  },
];

const ROLES = [
  {
    icon: Users,
    role: "Beneficiary",
    body: "Answers an interview by voice, sees their matches, applies, and follows their own progress.",
  },
  {
    icon: UserCog,
    role: "Government officer",
    body: "Reviews intake, accepts or rejects recommendations, and plans capacity against district demand.",
  },
  {
    icon: Building2,
    role: "Training provider",
    body: "Manages programmes and seats, confirms enrolment, and issues assessment results.",
  },
  {
    icon: ShieldCheck,
    role: "Administrator",
    body: "Manages users, roles, reference data and scheme-level reporting across districts.",
  },
];

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <GovTopBar />
      <SiteHeader />

      <main className="flex-1">
        {/* ── Hero ───────────────────────────────────────── */}
        <section className="relative overflow-hidden border-b border-border">
          <div className="pointer-events-none absolute inset-0 bg-grid mask-fade opacity-70" aria-hidden />
          <div className="container relative grid gap-14 py-20 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-28">
            <div className="animate-fade-up">
              <div className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-bold shadow-sm">
                <ShieldCheck className="size-3.5 text-primary" />
                <span className="text-muted-foreground">PM-AJAY · Problem statement SIH26097</span>
              </div>

              <h1 className="mt-6 font-display text-4xl font-bold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
                From a spoken sentence
                <span className="block text-gradient">to a livelihood.</span>
              </h1>

              <p className="mt-6 max-w-xl text-lg leading-8 text-muted-foreground">
                Kaushal AI interviews Scheduled Caste beneficiaries by voice in their own
                language, turns the conversation into an auditable skills profile, and matches it
                to NSQF-aligned training that local demand can actually absorb.
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                <Button asChild size="lg">
                  <Link href="/login">
                    Sign in to the portal <ArrowRight className="size-4" />
                  </Link>
                </Button>
                <Button asChild size="lg" variant="outline">
                  <a href="#how">See how it works</a>
                </Button>
              </div>

              <dl className="mt-12 grid max-w-lg grid-cols-3 gap-4 border-t border-border pt-8">
                {[
                  { value: "5", label: "interview languages" },
                  { value: "9", label: "scoring factors" },
                  { value: "4", label: "role-based views" },
                ].map((item) => (
                  <div key={item.label}>
                    <dt className="sr-only">{item.label}</dt>
                    <dd>
                      <div className="font-display text-3xl font-bold text-primary">{item.value}</div>
                      <div className="mt-1 text-xs font-semibold leading-tight text-muted-foreground">
                        {item.label}
                      </div>
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            {/* Product preview — the pipeline as the officer sees it */}
            <div className="animate-fade-up rounded-xl border border-border bg-card shadow-2xl [animation-delay:120ms]">
              <div className="flex items-center justify-between border-b border-border px-5 py-4">
                <div>
                  <div className="text-sm font-bold">Beneficiary journey</div>
                  <div className="text-xs font-semibold text-muted-foreground">
                    Ranchi district · Jharkhand
                  </div>
                </div>
                <span className="rounded-full bg-success/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-success">
                  Demo
                </span>
              </div>

              <div className="space-y-3 p-5">
                {PIPELINE.map((stage, index) => (
                  <div
                    key={stage.step}
                    className="grid grid-cols-[auto_1fr] items-start gap-3 rounded-lg border border-border bg-background p-3.5"
                  >
                    <span className="grid size-9 place-items-center rounded-md bg-primary/10 text-primary">
                      <stage.icon className="size-4" />
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-muted-foreground">{stage.step}</span>
                        <span className="text-sm font-bold">{stage.title}</span>
                      </div>
                      {index === 2 ? (
                        <div className="mt-2 flex items-center gap-2">
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-secondary">
                            <div className="h-full w-[94%] rounded-full bg-primary" />
                          </div>
                          <span className="text-xs font-bold text-primary">94%</span>
                        </div>
                      ) : (
                        <div className="mt-0.5 text-xs font-semibold text-muted-foreground">
                          {stage.preview}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── Problem ────────────────────────────────────── */}
        <Section
          id="problem"
          eyebrow="What we are solving"
          title="Skilling budgets exist. The routing does not."
          lead="PM-AJAY funds training for Scheduled Caste communities. The money is not the constraint — knowing who needs what, and whether it worked, is."
          className="border-b border-border bg-card"
        >
          <div className="grid gap-6 md:grid-cols-3">
            {PROBLEMS.map((item) => (
              <div
                key={item.title}
                className="rounded-xl border border-border bg-background p-6 transition-shadow hover:shadow-lg"
              >
                <span className="grid size-11 place-items-center rounded-lg bg-destructive/10 text-destructive">
                  <item.icon className="size-5" />
                </span>
                <div className="mt-5 text-xs font-bold uppercase tracking-wider text-destructive">
                  {item.stat}
                </div>
                <h3 className="mt-2 font-display text-lg font-bold">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.body}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* ── How it works ───────────────────────────────── */}
        <Section
          id="how"
          eyebrow="How it works"
          title="Five stages, one record."
          lead="Every stage writes to the same beneficiary record, so the officer's dashboard and the beneficiary's phone are always describing the same person."
        >
          <ol className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {PIPELINE.map((stage) => (
              <li
                key={stage.step}
                className="relative rounded-xl border border-border bg-card p-6 shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="grid size-11 place-items-center rounded-lg bg-primary text-primary-foreground">
                    <stage.icon className="size-5" />
                  </span>
                  <span className="font-display text-3xl font-bold text-border">{stage.step}</span>
                </div>
                <h3 className="mt-5 font-display text-lg font-bold">{stage.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{stage.body}</p>
              </li>
            ))}

            {/* Explainability is the differentiator, so it gets the last cell. */}
            <li className="rounded-xl border border-primary/25 bg-primary/5 p-6">
              <h3 className="font-display text-lg font-bold">Why it recommended that</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                The match score is a weighted sum, not a model's opinion. Every recommendation
                shows its factor breakdown, so an officer can defend — or overturn — it.
              </p>
              <ul className="mt-4 flex flex-wrap gap-1.5">
                {FACTORS.map((factor) => (
                  <li
                    key={factor}
                    className="rounded-md border border-border bg-card px-2 py-1 text-[11px] font-semibold text-muted-foreground"
                  >
                    {factor}
                  </li>
                ))}
              </ul>
            </li>
          </ol>
        </Section>

        {/* ── Platform ───────────────────────────────────── */}
        <Section
          id="platform"
          eyebrow="The platform"
          title="A government MIS, not a chatbot."
          lead="The conversation is the intake method. What it produces is a system of record officers can plan and report against."
          className="border-y border-border bg-card"
        >
          <div className="grid gap-6 sm:grid-cols-2">
            {MODULES.map((module) => (
              <div
                key={module.title}
                className="flex gap-4 rounded-xl border border-border bg-background p-6"
              >
                <span className="grid size-11 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                  <module.icon className="size-5" />
                </span>
                <div>
                  <h3 className="font-display text-lg font-bold">{module.title}</h3>
                  <p className="mt-1.5 text-sm leading-6 text-muted-foreground">{module.body}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* ── Roles ──────────────────────────────────────── */}
        <Section
          id="roles"
          eyebrow="For whom"
          title="Four roles, one pipeline."
          lead="Each sign-in sees only the workflow it is accountable for."
        >
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {ROLES.map((role) => (
              <div key={role.role} className="rounded-xl border border-border bg-card p-6 shadow-sm">
                <span className="grid size-11 place-items-center rounded-lg bg-secondary text-primary">
                  <role.icon className="size-5" />
                </span>
                <h3 className="mt-5 font-display text-base font-bold">{role.role}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{role.body}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* ── CTA ────────────────────────────────────────── */}
        <section className="border-t border-border bg-primary text-primary-foreground">
          <div className="container flex flex-col items-start justify-between gap-6 py-16 md:flex-row md:items-center">
            <div className="max-w-xl">
              <h2 className="font-display text-3xl font-bold tracking-tight">
                See the full journey end to end.
              </h2>
              <p className="mt-3 text-primary-foreground/80">
                Sign in with a demo role to walk the seeded Ramesh Kumar journey — interview,
                recommendation, enrolment and outcome.
              </p>
            </div>
            <Button asChild size="lg" variant="secondary" className="shrink-0">
              <Link href="/login">
                Open the portal <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
