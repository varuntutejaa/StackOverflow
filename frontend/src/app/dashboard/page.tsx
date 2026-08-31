"use client";

import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

import { Donut, GroupedBar, TrendArea } from "@/components/charts";
import { KpiCard, KpiSkeleton } from "@/components/kpi-card";
import { PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress, Skeleton } from "@/components/ui/misc";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useDemoPointer, useOverview } from "@/lib/hooks";
import { formatNumber, titleCase } from "@/lib/utils";

export default function OverviewPage() {
  const { data, isLoading } = useOverview();
  const { data: demo } = useDemoPointer();

  const langData = data
    ? Object.entries(data.language_split).map(([k, v]) => ({ name: titleCase(k), value: v }))
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Programme Overview"
        description="Live view of the KaushAI livelihood & skilling pipeline under PM-AJAY."
        actions={
          demo?.beneficiary_id && (
            <Button asChild>
              <Link href={`/dashboard/beneficiaries/${demo.beneficiary_id}`}>
                <Sparkles className="size-4" /> Open demo journey — {demo.name}
              </Link>
            </Button>
          )
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => <KpiSkeleton key={i} />)
          : data?.kpis.map((k) => (
              <KpiCard key={k.key} label={k.label} value={k.value} unit={k.unit} delta={k.delta_pct} />
            ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Enrolment trend</CardTitle>
            <CardDescription>Monthly training applications submitted</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-60 w-full" />
            ) : (
              <TrendArea data={data?.enrollment_trend ?? []} xKey="period" yKey="value" label="Applications" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Interview language mix</CardTitle>
            <CardDescription>Beneficiary preferred language</CardDescription>
          </CardHeader>
          <CardContent>{isLoading ? <Skeleton className="h-56 w-full" /> : <Donut data={langData} />}</CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Journey funnel</CardTitle>
            <CardDescription>Conversion at each stage</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading
              ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-9 w-full" />)
              : data?.funnel.map((f, i) => (
                  <div key={f.stage}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">{f.stage}</span>
                      <span className="tabular-nums text-muted-foreground">
                        {formatNumber(f.count)} {i > 0 && <span className="ml-1 text-xs">({f.conversion_from_previous}%)</span>}
                      </span>
                    </div>
                    <Progress
                      className="mt-1.5"
                      value={data.funnel[0].count ? (f.count / data.funnel[0].count) * 100 : 0}
                    />
                  </div>
                ))}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Top skill-gap sectors</CardTitle>
            <CardDescription>District demand vs trained supply (higher gap = priority)</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-72 w-full" />
            ) : (
              <GroupedBar
                data={(data?.skill_demand ?? []).slice(0, 6).map((s) => ({
                  skill: s.skill.length > 16 ? s.skill.slice(0, 15) + "…" : s.skill,
                  Demand: s.demand_score,
                  Supply: s.supply_score,
                }))}
                xKey="skill"
                bars={[
                  { key: "Demand", label: "Demand", color: "#0B3D91" },
                  { key: "Supply", label: "Supply", color: "#FF9933" },
                ]}
              />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>District-wise statistics</CardTitle>
            <CardDescription>{data?.notes}</CardDescription>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link href="/dashboard/map">
              Open map <ArrowRight className="size-4" />
            </Link>
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <THead>
              <TR>
                <TH>District</TH>
                <TH>Beneficiaries</TH>
                <TH>Interviews</TH>
                <TH>In training</TH>
                <TH>Certified</TH>
                <TH>Placed</TH>
                <TH>Placement rate</TH>
              </TR>
            </THead>
            <TBody>
              {isLoading
                ? Array.from({ length: 6 }).map((_, i) => (
                    <TR key={i}>
                      <TD colSpan={7}>
                        <Skeleton className="h-6 w-full" />
                      </TD>
                    </TR>
                  ))
                : data?.district_stats.slice(0, 10).map((d) => (
                    <TR key={d.district}>
                      <TD className="font-medium">{d.district}</TD>
                      <TD className="tabular-nums">{d.beneficiaries}</TD>
                      <TD className="tabular-nums">{d.interviews_done}</TD>
                      <TD className="tabular-nums">{d.in_training}</TD>
                      <TD className="tabular-nums">{d.certified}</TD>
                      <TD className="tabular-nums">{d.placed}</TD>
                      <TD className="tabular-nums">{d.placement_rate}%</TD>
                    </TR>
                  ))}
            </TBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
