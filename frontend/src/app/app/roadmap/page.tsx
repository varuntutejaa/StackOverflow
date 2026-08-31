"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Circle } from "lucide-react";

import { RecommendationCard } from "@/components/recommendation-card";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress, Skeleton } from "@/components/ui/misc";
import { apiFetch } from "@/lib/api";
import { useApplications, useRecommendations } from "@/lib/hooks";
import type { Beneficiary } from "@/lib/types";
import { titleCase } from "@/lib/utils";

const JOURNEY = ["interview_done", "recommended", "in_training", "certified", "placed"];

export default function RoadmapPage() {
  const [b, setB] = useState<Beneficiary | null>(null);
  const { data: recs } = useRecommendations(b?.id);
  const { data: apps } = useApplications(b ? { beneficiary_id: b.id } : {});

  useEffect(() => {
    (async () => {
      try {
        setB(await apiFetch<Beneficiary>("/beneficiaries/me"));
      } catch {
        const demo = await apiFetch<{ beneficiary_id: string | null }>("/meta/demo", { auth: false });
        if (demo.beneficiary_id) setB(await apiFetch<Beneficiary>(`/beneficiaries/${demo.beneficiary_id}`));
      }
    })();
  }, []);

  if (!b) return <Skeleton className="h-96 w-full" />;

  const currentIdx = JOURNEY.indexOf(b.status);
  const top = recs?.items?.find((r) => r.is_accepted) ?? recs?.items?.[0];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-bold">Your livelihood roadmap</h1>
        <p className="mt-1 text-sm text-muted-foreground">{b.full_name} · {b.district ?? "—"}</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Journey progress</CardTitle></CardHeader>
        <CardContent>
          <ol className="space-y-3">
            {JOURNEY.map((stage, i) => {
              const done = i <= currentIdx;
              return (
                <li key={stage} className="flex items-center gap-3">
                  {done ? <CheckCircle2 className="size-5 text-success" /> : <Circle className="size-5 text-muted-foreground" />}
                  <span className={done ? "font-medium" : "text-muted-foreground"}>{titleCase(stage)}</span>
                  {i === currentIdx && <StatusBadge status={b.status} />}
                </li>
              );
            })}
          </ol>
          <Progress className="mt-4" value={((currentIdx + 1) / JOURNEY.length) * 100} />
        </CardContent>
      </Card>

      {apps?.items?.map((a) => (
        <Card key={a.id}>
          <CardHeader><CardTitle>{a.program?.title}</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="text-muted-foreground">{a.program?.provider?.name} · {a.program?.location?.district}</p>
            <div className="flex items-center justify-between"><span>Training progress</span><span>{Math.round(a.progress_pct)}%</span></div>
            <Progress value={a.progress_pct} />
            <div className="flex items-center justify-between"><span>Attendance</span><span>{Math.round(a.attendance_pct)}%</span></div>
            <Progress value={a.attendance_pct} indicatorClassName="bg-accent" />
            {a.certificate_number && <p className="pt-1 text-success">Certificate: {a.certificate_number}</p>}
          </CardContent>
        </Card>
      ))}

      {top && (
        <div>
          <h2 className="mb-3 font-display text-lg font-semibold">Your primary pathway</h2>
          <RecommendationCard rec={top} />
        </div>
      )}
    </div>
  );
}
