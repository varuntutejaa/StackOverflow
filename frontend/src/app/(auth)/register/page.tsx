"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AlertCircle, ArrowRight, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";

import { GoogleMark } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label, NativeSelect } from "@/components/ui/misc";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Role } from "@/lib/types";

const ROLES: { value: Role; label: string }[] = [
  { value: "beneficiary", label: "Beneficiary" },
  { value: "training_provider", label: "Training Provider" },
  { value: "gov_officer", label: "Government Officer" },
  { value: "admin", label: "Administrator" },
];

export default function RegisterPage() {
  const { register, loginWithGoogle } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    phone: "",
    role: "beneficiary" as Role,
    organisation: "",
    district: "",
  });

  const set = (k: string, v: string) => {
    setForm((f) => ({ ...f, [k]: v }));
    setError(null);
  };

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await register({ ...form, phone: form.phone || undefined, organisation: form.organisation || undefined, district: form.district || undefined });
      toast.success("Account created. A verification email has been queued (see dev token in API logs).");
      router.push(user.role === "beneficiary" ? "/app/assistant" : "/dashboard");
    } catch (err) {
      // Kept on screen rather than only toasted — the user needs it visible
      // while they correct the field it refers to.
      setError(err instanceof ApiError ? String(err.detail) : "Registration failed. Please try again.");
      setLoading(false);
    }
  }

  async function googleSignIn() {
    setLoading(true);
    try {
      await loginWithGoogle();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-up failed");
      setLoading(false);
    }
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold tracking-tight">Request access</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Create a Kaushal AI account. Your role decides which workflow you see.
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

      <form onSubmit={submit} className="space-y-4" noValidate>
        <div className="space-y-2">
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" required autoFocus className="h-11" value={form.full_name} onChange={(e) => set("full_name", e.target.value)} placeholder="e.g. Ramesh Kumar" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Official email</Label>
          <Input id="email" type="email" required className="h-11" value={form.email} onChange={(e) => set("email", e.target.value)} placeholder="you@dept.gov.in" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Input
                id="password"
                type={revealed ? "text" : "password"}
                required
                minLength={8}
                className="h-11 pr-11"
                value={form.password}
                onChange={(e) => set("password", e.target.value)}
                placeholder="At least 8 characters"
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
          <div className="space-y-2">
            <Label htmlFor="phone">Phone (optional)</Label>
            <Input id="phone" className="h-11" value={form.phone} onChange={(e) => set("phone", e.target.value)} placeholder="10-digit mobile" />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="role">Role</Label>
          <NativeSelect id="role" className="h-11 w-full" value={form.role} onChange={(e) => set("role", e.target.value)}>
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </NativeSelect>
        </div>
        {/* Only officers and providers belong to an organisation, so these
            appear when the role actually needs them. */}
        {(form.role === "training_provider" || form.role === "gov_officer") && (
          <div className="grid animate-fade-in gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="organisation">Organisation</Label>
              <Input id="organisation" className="h-11" value={form.organisation} onChange={(e) => set("organisation", e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="district">District</Label>
              <Input id="district" className="h-11" value={form.district} onChange={(e) => set("district", e.target.value)} />
            </div>
          </div>
        )}
        <Button type="submit" size="lg" className="w-full" loading={loading}>
          Create account <ArrowRight className="size-4" />
        </Button>
      </form>

      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">or</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <Button type="button" variant="outline" size="lg" className="w-full" onClick={googleSignIn} disabled={loading}>
        <GoogleMark />
        Continue with Google
      </Button>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already registered?{" "}
        <Link href="/login" className="font-semibold text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}
