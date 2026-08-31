"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { InterviewConsole } from "@/components/interview-console";
import { RecommendationCard } from "@/components/recommendation-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, NativeSelect, Skeleton } from "@/components/ui/misc";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useConfig, useGenerateRecommendations, useInterviews, useRecommendations } from "@/lib/hooks";
import type { Beneficiary } from "@/lib/types";

export default function AssistantPage() {
  const { user, loading } = useAuth();
  const { data: config } = useConfig();
  const [beneficiary, setBeneficiary] = useState<Beneficiary | null>(null);
  const [resolving, setResolving] = useState(true);
  const [interviewId, setInterviewId] = useState<string | null>(null);
  const [language, setLanguage] = useState("hi");

  const { data: interviews } = useInterviews(beneficiary ? { beneficiary_id: beneficiary.id, page_size: 5 } : {});
  const { data: recs, refetch: refetchRecs } = useRecommendations(beneficiary?.id);
  const generate = useGenerateRecommendations();

  useEffect(() => {
    if (loading) return;
    (async () => {
      setResolving(true);
      try {
        if (user) {
          try {
            const mine = await apiFetch<Beneficiary>("/beneficiaries/me");
            setBeneficiary(mine);
            setLanguage(mine.preferred_language);
            return;
          } catch {
            /* no linked record — fall back to demo */
          }
        }
        const demo = await apiFetch<{ beneficiary_id: string | null }>("/meta/demo", { auth: false });
        if (demo.beneficiary_id) {
          const b = await apiFetch<Beneficiary>(`/beneficiaries/${demo.beneficiary_id}`);
          setBeneficiary(b);
          setLanguage(b.preferred_language);
        }
      } finally {
        setResolving(false);
      }
    })();
  }, [user, loading]);

  useEffect(() => {
    const open = interviews?.items?.find((i) => i.status !== "completed");
    if (open) setInterviewId(open.id);
  }, [interviews]);

  const completedInterview = interviews?.items?.find((i) => i.status === "completed");

  async function start() {
    if (!beneficiary) return;
    try {
      const iv = await apiFetch<{ id: string }>("/interviews", {
        method: "POST",
        body: { beneficiary_id: beneficiary.id, language },
      });
      setInterviewId(iv.id);
    } catch {
      toast.error("Could not start — you may need to sign in as a beneficiary.");
    }
  }

  if (loading || resolving) return <Skeleton className="h-96 w-full" />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-bold">Your KaushAI livelihood assistant</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Answer a few questions by voice or text in your language. KaushAI will build your profile and
          suggest the best skills and training for you.
        </p>
        {beneficiary?.is_demo && (
          <Badge variant="warning" className="mt-2">
            DEMO/SIMULATED — walkthrough for {beneficiary.full_name}
          </Badge>
        )}
      </div>

      {!beneficiary ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No beneficiary profile is linked to your account yet. Ask your welfare officer to register
            you, or <Link href="/login" className="text-primary underline">sign in</Link> as the demo
            beneficiary.
          </CardContent>
        </Card>
      ) : interviewId ? (
        <InterviewConsole
          interviewId={interviewId}
          onComplete={async () => {
            await generate.mutateAsync({ beneficiary_id: beneficiary.id, top_n: 5, persist: true });
            refetchRecs();
          }}
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>{completedInterview ? "Start a new interview" : "Start your interview"}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-3">
            <NativeSelect value={language} onChange={(e) => setLanguage(e.target.value)}>
              {config?.languages.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </NativeSelect>
            <Button onClick={start}>
              <Sparkles className="size-4" /> Begin voice interview
            </Button>
          </CardContent>
        </Card>
      )}

      {recs?.items && recs.items.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg font-semibold">Your recommended livelihood pathways</h2>
            <Button asChild variant="outline" size="sm">
              <Link href="/app/roadmap">
                Full roadmap <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>
          {recs.items.slice(0, 2).map((r) => (
            <RecommendationCard key={r.id} rec={r} />
          ))}
        </div>
      )}
    </div>
  );
}
