"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/misc";
import { apiFetch } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [devLink, setDevLink] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await apiFetch<{ detail: string; verification_url?: string | null; token?: string | null }>(
        "/auth/forgot-password",
        { method: "POST", auth: false, body: { email } },
      );
      setSent(true);
      setDevLink(res.verification_url || (res.token ? `/reset-password?token=${res.token}` : null));
      toast.success(res.detail);
    } catch {
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="animate-fade-in">
      <h1 className="font-display text-2xl font-bold">Reset your password</h1>
      <p className="mt-1 text-sm text-muted-foreground">We&apos;ll send a reset link to your email.</p>

      <form onSubmit={submit} className="mt-6 space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <Button type="submit" className="w-full" loading={loading}>
          Send reset link
        </Button>
      </form>

      {sent && (
        <div className="mt-4 rounded-lg border border-dashed border-border p-3 text-sm">
          <p className="text-muted-foreground">
            If an account exists, a link has been sent. No email provider is configured in this
            prototype, so use the link below (DEV only):
          </p>
          {devLink ? (
            <Link href={devLink} className="mt-2 block break-all font-medium text-primary hover:underline">
              {devLink}
            </Link>
          ) : (
            <p className="mt-2 text-xs">Check the backend logs for the reset token.</p>
          )}
        </div>
      )}

      <p className="mt-4 text-center text-sm text-muted-foreground">
        <Link href="/login" className="font-medium text-primary hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
