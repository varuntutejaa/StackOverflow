"use client";

import { GroupedBar } from "@/components/charts";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/shell/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, Skeleton } from "@/components/ui/misc";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useOutcomeDashboard, useOutcomes } from "@/lib/hooks";
import { formatCurrency, relativeTime, titleCase } from "@/lib/utils";

export default function OutcomesPage() {
  const { data, isLoading } = useOutcomeDashboard();
  const { data: outcomes } = useOutcomes({ page_size: 25, sort: "-created_at" });

  return (
    <div className="space-y-5">
      <PageHeader
        title="Outcome Tracking"
        description="Interview → Recommendation → Training → Certification → Employment / Self-employment, measured end to end."
      />

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Completion rate" value={data?.completion_rate ?? 0} unit="percent" />
            <KpiCard label="Placement rate" value={data?.placement_rate ?? 0} unit="percent" />
            <KpiCard label="Self-employment rate" value={data?.self_employment_rate ?? 0} unit="percent" />
            <KpiCard
              label="Avg income improvement"
              value={data?.avg_income_improvement_pct ?? 0}
              unit="percent"
              hint={`${formatCurrency(data?.avg_income_before ?? 0)} → ${formatCurrency(data?.avg_income_after ?? 0)}`}
            />
          </div>

          <Card>
            <CardHeader><CardTitle>District performance</CardTitle></CardHeader>
            <CardContent>
              <GroupedBar
                data={(data?.district_performance ?? []).slice(0, 10).map((d) => ({
                  district: d.district,
                  Certified: d.certified,
                  Placed: d.placed,
                  "Self-employed": d.self_employed,
                }))}
                xKey="district"
                stacked
                bars={[
                  { key: "Certified", label: "Certified", color: "#0B3D91" },
                  { key: "Placed", label: "Placed", color: "#138808" },
                  { key: "Self-employed", label: "Self-employed", color: "#FF9933" },
                ]}
              />
            </CardContent>
          </Card>

          <Card className="p-0">
            <CardHeader><CardTitle>Recent outcomes</CardTitle></CardHeader>
            <CardContent className="p-0">
              <Table>
                <THead>
                  <TR><TH>Stage</TH><TH>Type</TH><TH>Employer / venture</TH><TH>District</TH><TH>Income change</TH><TH>Verified</TH><TH>When</TH></TR>
                </THead>
                <TBody>
                  {outcomes?.items.map((o) => (
                    <TR key={o.id}>
                      <TD>{titleCase(o.stage)}</TD>
                      <TD>{o.outcome_type ? titleCase(o.outcome_type) : "—"}</TD>
                      <TD className="text-muted-foreground">{o.employer_or_venture ?? "—"}</TD>
                      <TD>{o.district ?? "—"}</TD>
                      <TD className="tabular-nums">
                        {o.income_before && o.income_after
                          ? `${formatCurrency(o.income_before)} → ${formatCurrency(o.income_after)}`
                          : "—"}
                      </TD>
                      <TD><Badge variant={o.is_verified ? "success" : "secondary"}>{o.is_verified ? "Verified" : "Reported"}</Badge></TD>
                      <TD className="text-muted-foreground">{relativeTime(o.created_at)}</TD>
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
