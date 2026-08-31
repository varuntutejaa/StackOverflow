"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/misc";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const DEMO_ACCOUNTS = [
  { label: "Administrator", email: "admin@kaushai.gov.in", password: "KaushAI@2026" },
  { label: "Government Officer", email: "officer@kaushai.gov.in", password: "Officer@2026" },
  { label: "Training Provider", email: "provider@kaushai.gov.in", password: "Provider@2026" },
  { label: "Beneficiary", email: "ramesh@kaushai.gov.in", password: "Ramesh@2026" },
];

function LoginInner() {
  const { login, loginWithGoogle } = useAuth();
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success(`Welcome back, ${user.full_name.split(" ")[0]}`);
      const next = params.get("next");
      router.push(next && next.startsWith("/") ? next : user.role === "beneficiary" ? "/app/assistant" : "/dashboard");
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Sign in failed");
    } finally {
      setLoading(false);
    }
  }

  async function googleSignIn() {
    setLoading(true);
    try {
      await loginWithGoogle();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Google sign-in failed");
      setLoading(false);
    }
  }

  return (
    <div className="animate-fade-in">
      <h1 className="font-display text-2xl font-bold">Sign in to KaushAI</h1>
      <p className="mt-1 text-sm text-muted-foreground">Admin & government portal access</p>

      <form onSubmit={submit} className="mt-6 space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="username" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@dept.gov.in" />
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link href="/forgot-password" className="text-xs font-medium text-primary hover:underline">
              Forgot password?
            </Link>
          </div>
          <Input id="password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
        </div>
        <Button type="submit" className="w-full" loading={loading}>
          Sign in
        </Button>
      </form>

      <div className="my-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-xs font-medium uppercase text-muted-foreground">or</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <Button type="button" variant="outline" className="w-full" onClick={googleSignIn} disabled={loading}>
        Sign in with Google
      </Button>

      <p className="mt-4 text-center text-sm text-muted-foreground">
        No account?{" "}
        <Link href="/register" className="font-medium text-primary hover:underline">
          Create one
        </Link>
      </p>

      <div className="mt-8 rounded-lg border border-dashed border-border p-3">
        <p className="text-xs font-semibold text-muted-foreground">DEMO/SIMULATED logins — click to fill</p>
        <div className="mt-2 grid grid-cols-2 gap-2">
          {DEMO_ACCOUNTS.map((a) => (
            <button
              key={a.email}
              type="button"
              onClick={() => {
                setEmail(a.email);
                setPassword(a.password);
              }}
              className="rounded-md border border-border bg-card px-2.5 py-2 text-left text-xs transition-colors hover:border-primary hover:bg-secondary"
            >
              <div className="font-medium">{a.label}</div>
              <div className="truncate text-muted-foreground">{a.email}</div>
            </button>
          ))}
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
