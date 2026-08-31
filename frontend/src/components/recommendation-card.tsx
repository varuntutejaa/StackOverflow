"use client";

import { CheckCircle2, GraduationCap, Route, Target, TriangleAlert } from "lucide-react";

import { FactorRadar } from "@/components/charts";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge, Progress } from "@/components/ui/misc";
import type { Recommendation } from "@/lib/types";
import { formatCurrency, titleCase } from "@/lib/utils";

export function RecommendationCard({
  rec,
  onApply,
  applying,
}: {
  rec: Recommendation;
  onApply?: (rec: Recommendation) => void;
  applying?: boolean;
}) {
  const radar = Object.entries(rec.factor_scores).map(([k, v]) => ({
    factor: titleCase(k).replace(" Compatibility", "").replace("Employment ", "Emp "),
    score: v,
  }));

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="grid size-7 place-items-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                #{rec.rank}
              </span>
              <h3 className="font-display text-base font-semibold">{rec.skill?.name}</h3>
              {rec.is_accepted && <Badge variant="success">Accepted</Badge>}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {rec.skill?.sector} · NSQF Level {rec.skill?.nsqf_level}
              {rec.skill?.avg_wage_monthly ? ` · ~${formatCurrency(rec.skill.avg_wage_monthly)}/mo` : ""}
            </p>
          </div>
          <div className="text-right">
            <div className="font-display text-3xl font-bold text-primary tabular-nums">
              {rec.match_score.toFixed(0)}
              <span className="text-base">%</span>
            </div>
            <p className="text-xs text-muted-foreground">match score</p>
          </div>
        </div>

        <div className="mt-4 grid gap-5 md:grid-cols-[1fr_260px]">
          <div className="space-y-4">
            <div>
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Target className="size-3.5" /> Why this match
              </p>
              <ul className="mt-1.5 space-y-1 text-sm">
                {rec.reasons.map((r, i) => (
                  <li key={i} className="flex gap-2">
                    <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-success" /> {r}
                  </li>
                ))}
              </ul>
            </div>

            {rec.skill_gaps.length > 0 && (
              <div>
                <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  <TriangleAlert className="size-3.5" /> Skill gaps to bridge
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {rec.skill_gaps.map((g, i) => (
                    <Badge key={i} variant="warning">{g}</Badge>
                  ))}
                </div>
              </div>
            )}

            <div>
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <Route className="size-3.5" /> Career pathway
              </p>
              <ol className="mt-2 space-y-2">
                {rec.career_pathway.map((s) => (
                  <li key={s.step} className="flex gap-3 text-sm">
                    <span className="grid size-5 shrink-0 place-items-center rounded-full bg-secondary text-[10px] font-bold">
                      {s.step}
                    </span>
                    <span>
                      <span className="font-medium">{s.title}</span> — <span className="text-muted-foreground">{s.detail}</span>
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Factor breakdown</p>
            <FactorRadar data={radar} />
            {rec.suggested_program && (
              <div className="mt-2 rounded-lg border border-border bg-secondary/40 p-3 text-xs">
                <p className="flex items-center gap-1.5 font-semibold">
                  <GraduationCap className="size-3.5" /> Suggested training
                </p>
                <p className="mt-1">{rec.suggested_program.title}</p>
                <p className="text-muted-foreground">
                  {rec.suggested_program.provider?.name} · {rec.suggested_program.seats_available} seats ·{" "}
                  {rec.suggested_program.duration_weeks}w
                </p>
              </div>
            )}
          </div>
        </div>

        {onApply && (
          <div className="mt-4 flex justify-end">
            <Button onClick={() => onApply(rec)} loading={applying} disabled={!rec.suggested_program}>
              <GraduationCap className="size-4" /> Apply to suggested training
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
