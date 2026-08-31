"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import { toast } from "sonner";

import { RecommendationCard } from "@/components/recommendation-card";
import { PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState, Label, NativeSelect, Skeleton } from "@/components/ui/misc";
import { useBeneficiaries, useGenerateRecommendations, useRecommendations, useRecommendationWeights } from "@/lib/hooks";
import { titleCase } from "@/lib/utils";

export default function RecommendationsPage() {
  const { data: bens } = useBeneficiaries({ page_size: 100, status: "interview_done" });
  const { data: recommendedBens } = useBeneficiaries({ page_size: 100, status: "recommended" });
  const [selected, setSelected] = useState("");
  const { data: recs, isLoading } = useRecommendations(selected || undefined);
  const { data: weights } = useRecommendationWeights();
  const generate = useGenerateRecommendations();

  const options = [...(bens?.items ?? []), ...(recommendedBens?.items ?? [])];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Skill Recommendations"
        description="Transparent weighted-scoring engine — every point in a match score is attributable to a named factor."
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardContent className="flex flex-wrap items-end gap-3 py-4">
            <div className="min-w-[240px] flex-1 space-y-1.5">
              <Label>Beneficiary</Label>
              <NativeSelect className="w-full" value={selected} onChange={(e) => setSelected(e.target.value)}>
                <option value="">— select a beneficiary —</option>
                {options.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.full_name} · {b.district ?? "—"} · {titleCase(b.status)}
                  </option>
                ))}
              </NativeSelect>
            </div>
            <Button
              disabled={!selected}
              loading={generate.isPending}
              onClick={async () => {
                await generate.mutateAsync({ beneficiary_id: selected, top_n: 5, persist: true });
                toast.success("Recommendations generated");
              }}
            >
              <Sparkles className="size-4" /> Generate
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Engine weights</CardTitle></CardHeader>
          <CardContent className="space-y-1.5 text-xs">
            {weights &&
              Object.entries(weights.weights).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-2">
                  <span className="text-muted-foreground" title={weights.description[k]}>{titleCase(k)}</span>
                  <span className="font-mono">{(v * 100).toFixed(0)}%</span>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>

      {!selected ? (
        <EmptyState icon={Sparkles} title="Select a beneficiary" description="Pick a beneficiary to view or generate recommendations." />
      ) : isLoading ? (
        <Skeleton className="h-72 w-full" />
      ) : recs?.items?.length ? (
        <div className="space-y-4">
          {recs.items.map((r) => (
            <RecommendationCard key={r.id} rec={r} />
          ))}
        </div>
      ) : (
        <EmptyState icon={Sparkles} title="No recommendations" description="Click Generate to run the recommendation engine." />
      )}
    </div>
  );
}
