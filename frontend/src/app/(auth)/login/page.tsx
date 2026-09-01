"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { AlertCircle, ArrowRight, Building2, Eye, EyeOff, ShieldCheck, UserCog, Users } from "lucide-react";
import { toast } from "sonner";

import { GoogleMark } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/misc";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const DEMO_ACCOUNTS = [
  { icon: ShieldCheck, label: "Administrator", email: "admin@kaushai.gov.in", password: "Admin@2026" },
  { icon: UserCog, label: "Gov. officer", email: "officer@kaushai.gov.in", password: "Officer@2026" },
  { icon: Building2, label: "Provider", email: "provider@kaushai.gov.in", password: "Provider@2026" },
  { icon: Users, label: "Beneficiary", email: "ramesh@kaushai.gov.in", password: "Ramesh@2026" },
];

function LoginInner() {
  const { login, loginWithGoogle } = useAuth();
  const router = useRouter();
  const params = useSearchParams();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [revealed, setRevealed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.full_name.split(" ")[0]}`);
      const next = params.get("next");
      router.push(
        next && next.startsWith("/")
          ? next
          : user.role === "beneficiary"
            ? "/app/assistant"
            : "/dashboard",
      );
    } catch (err) {
      // Shown inline as well as toasted: a sign-in failure has to stay on screen
      // while the user retypes, and a toast has usually gone by then.
      setError(err instanceof ApiError ? String(err.detail) : "Sign in failed. Please try again.");
      setLoading(false);
    }
  }

  async function googleSignIn() {
    setLoading(true);
    setError(null);
    try {
      await loginWithGoogle();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed");
      setLoading(false);
    }
  }

  function fillDemo(account: (typeof DEMO_ACCOUNTS)[number]) {
    setEmail(account.email);
    setPassword(account.password);
    setError(null);
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold tracking-tight">Sign in</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Government and administrator access to the Kaushal AI portal.
        </p>
      </div>

      {error ? (
        <div
          role="alert"
          className="mb-5 flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3"
        >
          <AlertCircle className="mt-0.5 size-4 shrink-0 text-destructive" />
          <p className="text-sm font-medium text-destructive">{error}</p>
        </div>
      ) : null}

      <form onSubmit={submit} className="space-y-5" noValidate>
        <div className="space-y-2">
          <Label htmlFor="email">Official email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            required
            autoFocus
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@dept.gov.in"
            aria-invalid={Boolean(error)}
            className="h-11"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link
              href="/forgot-password"
              className="text-xs font-semibold text-primary hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Input
              id="password"
              type={revealed ? "text" : "password"}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              aria-invalid={Boolean(error)}
              className="h-11 pr-11"
            />
            <button
              type="button"
              onClick={() => setRevealed((v) => !v)}
              aria-label={revealed ? "Hide password" : "Show password"}
              className="absolute inset-y-0 right-0 grid w-11 place-items-center rounded-r-md text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {revealed ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
        </div>

        <Button type="submit" size="lg" className="w-full" loading={loading}>
          Sign in <ArrowRight className="size-4" />
        </Button>
      </form>

      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
          or
        </span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <Button
        type="button"
        variant="outline"
        size="lg"
        className="w-full"
        onClick={googleSignIn}
        disabled={loading}
      >
        <GoogleMark />
        Continue with Google
      </Button>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Need portal access?{" "}
        <Link href="/register" className="font-semibold text-primary hover:underline">
          Request an account
        </Link>
      </p>

      {/* Demo roles — this is a hackathon prototype, and an evaluator should be
          able to see all four workflows without hunting for credentials. */}
      <div className="mt-10 rounded-xl border border-border bg-secondary/50 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
            Demo roles
          </p>
          <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-warning">
            Simulated
          </span>
        </div>
        <p className="mt-1.5 text-xs text-muted-foreground">
          Select a role to fill its credentials, then sign in.
        </p>

        <div className="mt-3 grid grid-cols-2 gap-2">
          {DEMO_ACCOUNTS.map((account) => {
            const active = email === account.email;
            return (
              <button
                key={account.email}
                type="button"
                onClick={() => fillDemo(account)}
                aria-pressed={active}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg border bg-card px-3 py-2.5 text-left transition-all",
                  active
                    ? "border-primary ring-1 ring-primary"
                    : "border-border hover:border-primary/50 hover:bg-card/80",
                )}
              >
                <account.icon
                  className={cn("size-4 shrink-0", active ? "text-primary" : "text-muted-foreground")}
                />
                <span className="min-w-0">
                  <span className="block truncate text-xs font-bold">{account.label}</span>
                  <span className="block truncate text-[11px] text-muted-foreground">
                    {account.email.split("@")[0]}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}
