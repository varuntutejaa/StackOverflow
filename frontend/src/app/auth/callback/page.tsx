"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { toast } from "sonner";

import { apiFetch, tokenStore } from "@/lib/api";
import type { TokenPair } from "@/lib/types";
import { supabase } from "@/lib/supabase";

function CallbackInner() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    async function finish() {
      if (!supabase) {
        toast.error("Supabase Auth is not configured");
        router.replace("/login");
        return;
      }

      const { data, error } = await supabase.auth.getSession();
      const accessToken = data.session?.access_token;
      if (error || !accessToken) {
        toast.error(error?.message || "Google sign-in did not complete");
        router.replace("/login");
        return;
      }

      try {
        const pair = await apiFetch<TokenPair>("/auth/supabase", {
          method: "POST",
          auth: false,
          body: { access_token: accessToken },
        });
        tokenStore.set(pair);
        toast.success(`Welcome, ${pair.user.full_name.split(" ")[0]}`);
        const next = params.get("next");
        router.replace(next && next.startsWith("/") ? next : pair.user.role === "beneficiary" ? "/app/assistant" : "/dashboard");
      } catch {
        toast.error("Could not connect Google account to KaushAI");
        router.replace("/login");
      }
    }

    finish();
  }, [params, router]);

  return (
    <div className="animate-fade-in">
      <h1 className="font-display text-2xl font-bold">Signing you in</h1>
      <p className="mt-1 text-sm text-muted-foreground">Connecting your Google account to KaushAI...</p>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={null}>
      <CallbackInner />
    </Suspense>
  );
}
