"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import {
  ArrowLeft,
  Briefcase,
  GraduationCap,
  Mic,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

import { InterviewConsole } from "@/components/interview-console";
import { RecommendationCard } from "@/components/recommendation-card";
import { PageHeader } from "@/components/shell/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, EmptyState, Separator, Skeleton } from "@/components/ui/misc";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { ApiError } from "@/lib/api";
import {
  useApplications,
  useBeneficiary,
  useCreateApplication,
  useCreateInterview,
  useGenerateRecommendations,
  useInterviews,
  useRecommendations,
} from "@/lib/hooks";
import type { Recommendation } from "@/lib/types";
import { formatCurrency, relativeTime, titleCase } from "@/lib/utils";

export default function BeneficiaryDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: b, isLoading, refetch } = useBeneficiary(id);
  const { data: interviews } = useInterviews({ beneficiary_id: id, page_size: 20 });
  const { data: recs, refetch: refetchRecs } = useRecommendations(id);
  const { data: apps } = useApplications({ beneficiary_id: id });

  const createInterview = useCreateInterview();
  const generate = useGenerateRecommendations();
  const createApp = useCreateApplication();

  const [activeInterview, setActiveInterview] = useState<string | null>(null);

  if (isLoading || !b) {
    return <Skeleton className="h-96 w-full" />;
  }

  const latestInterview = interviews?.items?.[0];
  const inProgress = interviews?.items?.find((i) => i.status !== "completed");

  async function startInterview() {
    try {
      const iv = await createInterview.mutateAsync({ beneficiary_id: id, language: b!.preferred_language });
      setActiveInterview(iv.id);
      toast.success("Interview started");
    } catch {
      toast.error("Could not start interview");
    }
  }

  async function runRecommendations() {
    try {
      await generate.mutateAsync({ beneficiary_id: id, top_n: 5, persist: true });
      toast.success("Recommendations generated");
      refetchRecs();
      refetch();
    } catch (e) {
      toast.error(e instanceof ApiError ? String(e.detail) : "Failed");
    }
  }

  async function apply(rec: Recommendation) {
    if (!rec.suggested_program) return;
    try {
      await createApp.mutateAsync({ beneficiary_id: id, program_id: rec.suggested_program.id, recommendation_id: rec.id });
      toast.success("Training application submitted");
      refetch();
    } catch (e) {
      toast.error(e instanceof ApiError ? String(e.detail) : "Could not apply");
    }
  }

  return (
    <div className="space-y-5">
      <Button variant="ghost" size="sm" onClick={() => router.push("/dashboard/beneficiaries")}>
        <ArrowLeft className="size-4" /> All beneficiaries
      </Button>

      <PageHeader
        title={b.full_name}
        description={`${b.district ?? "—"}${b.village ? ` · ${b.village}` : ""} · ${b.pmajay_id ?? "No PM-AJAY ID"}`}
        actions={
          <>
            <StatusBadge status={b.status} />
            {b.is_demo && <Badge variant="warning">DEMO/SIMULATED</Badge>}
          </>
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            {[
              ["Age", b.age ?? "—"],
              ["Gender", titleCase(b.gender)],
              ["Language", titleCase(b.preferred_language)],
              ["Education", titleCase(b.education_level)],
              ["Current occupation", b.current_occupation ? titleCase(b.current_occupation) : "—"],
              ["Family occupation", b.family_occupation ? titleCase(b.family_occupation) : "—"],
              ["Monthly income", b.monthly_income ? formatCurrency(b.monthly_income) : "—"],
              ["Mobility", titleCase(b.mobility)],
              ["Employment preference", titleCase(b.employment_preference)],
            ].map(([k, v]) => (
              <div key={k as string} className="flex justify-between gap-4">
                <span className="text-muted-foreground">{k}</span>
                <span className="text-right font-medium">{v as string}</span>
              </div>
            ))}
            <Separator className="my-3" />
            <MetaList label="Skills" values={b.skills} />
            <MetaList label="Interests" values={b.interests} />
            <MetaList label="Constraints" values={b.constraints} variant="warning" />
          </CardContent>
        </Card>

        <div className="lg:col-span-2">
          <Tabs defaultValue="interview">
            <TabsList>
              <TabsTrigger value="interview">Interview</TabsTrigger>
              <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
              <TabsTrigger value="applications">Training</TabsTrigger>
            </TabsList>

            <TabsContent value="interview">
              {activeInterview || inProgress ? (
                <InterviewConsole
                  interviewId={(activeInterview || inProgress?.id)!}
                  onComplete={() => {
                    refetch();
                    toast.message("Profile updated from interview — you can now generate recommendations");
                  }}
                />
              ) : latestInterview ? (
                <Card>
                  <CardHeader className="flex-row items-center justify-between">
                    <CardTitle>Completed interview</CardTitle>
                    <Button size="sm" variant="outline" onClick={startInterview} loading={createInterview.isPending}>
                      <Mic className="size-4" /> New interview
                    </Button>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      {relativeTime(latestInterview.created_at)} · {titleCase(latestInterview.language)} ·{" "}
                      {Math.round(latestInterview.completion_pct)}% complete
                    </p>
                    <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-secondary/50 p-3 text-xs">
                      {latestInterview.transcript}
                    </pre>
                  </CardContent>
                </Card>
              ) : (
                <EmptyState
                  icon={Mic}
                  title="No interview yet"
                  description="Run the AI voice interview to capture the beneficiary's livelihood profile."
                  action={<Button onClick={startInterview} loading={createInterview.isPending}><Mic className="size-4" /> Start voice interview</Button>}
                />
              )}
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  Explainable NSQF matching from the recommendation engine
                </p>
                <Button size="sm" onClick={runRecommendations} loading={generate.isPending}>
                  <Sparkles className="size-4" /> {recs?.items?.length ? "Regenerate" : "Generate"}
                </Button>
              </div>
              {recs?.items?.length ? (
                recs.items.map((r) => (
                  <RecommendationCard key={r.id} rec={r} onApply={apply} applying={createApp.isPending} />
                ))
              ) : (
                <EmptyState
                  icon={Sparkles}
                  title="No recommendations yet"
                  description="Generate skill recommendations once the interview / profile is ready."
                />
              )}
            </TabsContent>

            <TabsContent value="applications">
              {apps?.items?.length ? (
                <Card className="p-0">
                  <Table>
                    <THead>
                      <TR>
                        <TH>Program</TH>
                        <TH>Status</TH>
                        <TH>Progress</TH>
                        <TH>Certificate</TH>
                      </TR>
                    </THead>
                    <TBody>
                      {apps.items.map((a) => (
                        <TR key={a.id}>
                          <TD className="font-medium">{a.program?.title ?? a.program_id}</TD>
                          <TD><StatusBadge status={a.status} /></TD>
                          <TD className="tabular-nums">{Math.round(a.progress_pct)}%</TD>
                          <TD className="text-muted-foreground">{a.certificate_number ?? "—"}</TD>
                        </TR>
                      ))}
                    </TBody>
                  </Table>
                </Card>
              ) : (
                <EmptyState icon={GraduationCap} title="No training applications" description="Apply from a recommendation or the Training catalogue." />
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {b.ai_profile && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Briefcase className="size-4 text-primary" /> AI-extracted profile
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="overflow-auto rounded-lg bg-secondary/50 p-3 text-xs">
              {JSON.stringify(b.ai_profile, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MetaList({ label, values, variant }: { label: string; values: string[]; variant?: "warning" }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {values.length ? (
          values.map((v) => (
            <Badge key={v} variant={variant ?? "secondary"}>
              {titleCase(v)}
            </Badge>
          ))
        ) : (
          <span className="text-xs text-muted-foreground">None recorded</span>
        )}
      </div>
    </div>
  );
}
