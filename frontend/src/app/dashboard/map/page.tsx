"use client";

import { useMemo, useState } from "react";

import { HBar } from "@/components/charts";
import { LivelihoodMap } from "@/components/livelihood-map";
import { PageHeader } from "@/components/shell/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { NativeSelect, Skeleton } from "@/components/ui/misc";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useLivelihoodMap } from "@/lib/hooks";
import { formatNumber } from "@/lib/utils";

export default function MapPage() {
  const { data, isLoading } = useLivelihoodMap();
  const [sortBy, setSortBy] = useState<"beneficiaries" | "avg_gap_score" | "open_opportunities">("beneficiaries");

  const rows = useMemo(() => {
    const pts = [...(data?.points ?? [])];
    pts.sort((a, b) => Number(b[sortBy]) - Number(a[sortBy]));
    return pts;
  }, [data, sortBy]);

  const gapChart = rows
    .slice()
    .sort((a, b) => b.avg_gap_score - a.avg_gap_score)
    .slice(0, 8)
    .map((p) => ({ district: p.district, gap: p.avg_gap_score }));

  return (
    <div className="space-y-5">
      <PageHeader
        title="Livelihood Map"
        description="District-level beneficiary distribution, skill demand & supply, training centres, opportunities and skill gaps."
      />

      {isLoading ? (
        <Skeleton className="h-[520px] w-full" />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-4">
            {[
              ["Districts", data?.points.length ?? 0],
              ["Beneficiaries", data?.totals.beneficiaries ?? 0],
              ["Training centres", data?.totals.training_centers ?? 0],
              ["Open opportunities", data?.totals.open_opportunities ?? 0],
            ].map(([k, v]) => (
              <Card key={k as string} className="p-4">
                <p className="text-xs uppercase text-muted-foreground">{k}</p>
                <p className="mt-1 font-display text-2xl font-bold">{formatNumber(v as number)}</p>
              </Card>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-5">
            <Card className="lg:col-span-3">
              <CardHeader><CardTitle>District map · {data?.period}</CardTitle></CardHeader>
              <CardContent>
                <LivelihoodMap points={data?.points ?? []} />
              </CardContent>
            </Card>
            <Card className="lg:col-span-2">
              <CardHeader><CardTitle>Highest skill-gap districts</CardTitle></CardHeader>
              <CardContent>
                <HBar data={gapChart} categoryKey="district" valueKey="gap" height={300} />
              </CardContent>
            </Card>
          </div>

          <Card className="p-0">
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>District detail</CardTitle>
              <NativeSelect value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
                <option value="beneficiaries">Sort by beneficiaries</option>
                <option value="avg_gap_score">Sort by skill gap</option>
                <option value="open_opportunities">Sort by opportunities</option>
              </NativeSelect>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <THead>
                  <TR>
                    <TH>District</TH><TH>Beneficiaries</TH><TH>In training</TH><TH>Certified</TH><TH>Placed</TH>
                    <TH>Centres</TH><TH>Opportunities</TH><TH>Demand</TH><TH>Supply</TH><TH>Gap</TH>
                    <TH>Top gap skills</TH>
                  </TR>
                </THead>
                <TBody>
                  {rows.map((p) => (
                    <TR key={p.location_id}>
                      <TD className="font-medium">{p.district}</TD>
                      <TD className="tabular-nums">{p.beneficiaries}</TD>
                      <TD className="tabular-nums">{p.in_training}</TD>
                      <TD className="tabular-nums">{p.certified}</TD>
                      <TD className="tabular-nums">{p.placed}</TD>
                      <TD className="tabular-nums">{p.training_centers}</TD>
                      <TD className="tabular-nums">{p.open_opportunities}</TD>
                      <TD className="tabular-nums">{p.avg_demand_score}</TD>
                      <TD className="tabular-nums">{p.avg_supply_score}</TD>
                      <TD className="tabular-nums font-semibold">{p.avg_gap_score}</TD>
                      <TD className="text-xs text-muted-foreground">{p.top_gap_skills.join(", ") || "—"}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
