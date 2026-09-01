import Link from "next/link";
import type { ReactNode } from "react";

import { Logo } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Chrome shared by the public pages.
 *
 * Government services are judged on whether they look official before they are
 * judged on anything else, so the tricolour rule and the departmental line are
 * fixed furniture rather than decoration — they appear identically on the
 * landing page and behind the sign-in form.
 */

/** The tricolour rule that marks this as a government service. */
export function GovStripe({ className }: { className?: string }) {
  return <div className={cn("h-1 w-full gov-stripe", className)} aria-hidden />;
}

export function GovTopBar() {
  return (
    <>
      <GovStripe />
      <div className="border-b border-border bg-secondary/60">
        <div className="container flex h-9 items-center justify-between text-[11px] font-semibold text-muted-foreground">
          <span>Government of India · Ministry of Social Justice &amp; Empowerment</span>
          <span className="hidden sm:block">PM-AJAY · SIH26097 · Prototype</span>
        </div>
      </div>
    </>
  );
}

const NAV = [
  { href: "#problem", label: "The problem" },
  { href: "#how", label: "How it works" },
  { href: "#platform", label: "Platform" },
  { href: "#roles", label: "For whom" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-card/80 backdrop-blur-md">
      <div className="container flex h-16 items-center justify-between gap-6">
        <Link href="/" aria-label="Kaushal AI home">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild size="sm">
            <Link href="/register">Request access</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="container grid gap-8 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-4 max-w-sm text-sm leading-6 text-muted-foreground">
            Voice-first livelihood mapping and NSQF-aligned skilling recommendations for
            Scheduled Caste communities under PM-AJAY.
          </p>
        </div>

        <div>
          <h3 className="text-sm font-bold">Platform</h3>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            {NAV.map((item) => (
              <li key={item.href}>
                <a href={item.href} className="hover:text-foreground">
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-bold">Access</h3>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>
              <Link href="/login" className="hover:text-foreground">
                Officer sign in
              </Link>
            </li>
            <li>
              <Link href="/register" className="hover:text-foreground">
                Request access
              </Link>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="container flex flex-col gap-2 py-5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>
            Prototype for Smart India Hackathon 2026 · Problem statement SIH26097. Not an
            official Government of India system.
          </p>
          <p className="font-semibold">All seeded records are labelled DEMO / SIMULATED.</p>
        </div>
      </div>
    </footer>
  );
}

/** Consistent vertical rhythm and heading treatment for every landing section. */
export function Section({
  id,
  eyebrow,
  title,
  lead,
  children,
  className,
}: {
  id?: string;
  eyebrow?: string;
  title: ReactNode;
  lead?: ReactNode;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={cn("scroll-mt-20 py-20 sm:py-24", className)}>
      <div className="container">
        <div className="max-w-2xl">
          {eyebrow ? (
            <div className="text-xs font-bold uppercase tracking-widest text-primary">{eyebrow}</div>
          ) : null}
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">{title}</h2>
          {lead ? (
            <p className="mt-4 text-base leading-7 text-muted-foreground sm:text-lg">{lead}</p>
          ) : null}
        </div>
        {children ? <div className="mt-12">{children}</div> : null}
      </div>
    </section>
  );
}
