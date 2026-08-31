"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

function VerifyInner() {
  const token = useSearchParams().get("token") || "";
  const [state, setState] = useState<"pending" | "ok" | "error">("pending");

  useEffect(() => {
    if (!token) {
      setState("error");
      return;
    }
    apiFetch("/auth/verify-email", { method: "POST", auth: false, body: { token } })
      .then(() => setState("ok"))
      .catch(() => setState("error"));
  }, [token]);

  return (
    <div className="animate-fade-in text-center">
      <h1 className="font-display text-2xl font-bold">
        {state === "pending" ? "Verifying…" : state === "ok" ? "Email verified" : "Verification failed"}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        {state === "ok"
          ? "Your email address has been confirmed."
          : state === "error"
            ? "The link is invalid or expired. Request a new verification email from your profile."
            : "Please wait a moment."}
      </p>
      <Button asChild className="mt-6">
        <Link href="/dashboard">Continue</Link>
      </Button>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyInner />
    </Suspense>
  );
}
