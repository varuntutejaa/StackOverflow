"use client";

import { GroupedBar, HBar } from "@/components/charts";
import { PageHeader } from "@/components/shell/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, Skeleton } from "@/components/ui/misc";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useOverview } from "@/lib/hooks";

export default function SkillDemandPage() {
  const { data, isLoading } = useOverview();
  const sd = data?.skill_demand ?? [];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Skill Demand"
        description="Demand vs trained-supply across skills, aggregated from district signals. Positive gap = under-served skill (training priority)."
      />

      {isLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : (
        <>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Demand vs supply</CardTitle></CardHeader>
              <CardContent>
                <GroupedBar
                  data={sd.slice(0, 8).map((s) => ({
                    skill: s.skill.length > 14 ? s.skill.slice(0, 13) + "…" : s.skill,
                    Demand: s.demand_score,
                    Supply: s.supply_score,
                  }))}
                  xKey="skill"
                  bars={[
                    { key: "Demand", label: "Demand", color: "#0B3D91" },
                    { key: "Supply", label: "Supply", color: "#FF9933" },
                  ]}
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Largest skill gaps</CardTitle></CardHeader>
              <CardContent>
                <HBar data={sd.slice(0, 8).map((s) => ({ skill: s.skill, gap: s.gap_score }))} categoryKey="skill" valueKey="gap" />
              </CardContent>
            </Card>
          </div>

          <Card className="p-0">
            <CardHeader><CardTitle>All skills</CardTitle></CardHeader>
            <CardContent className="p-0">
              <Table>
                <THead>
                  <TR><TH>Skill</TH><TH>Sector</TH><TH>Demand</TH><TH>Supply</TH><TH>Gap</TH><TH>Open positions</TH><TH>Priority</TH></TR>
                </THead>
                <TBody>
                  {sd.map((s) => (
                    <TR key={s.skill}>
                      <TD className="font-medium">{s.skill}</TD>
                      <TD className="text-muted-foreground">{s.sector}</TD>
                      <TD className="tabular-nums">{s.demand_score}</TD>
                      <TD className="tabular-nums">{s.supply_score}</TD>
                      <TD className="tabular-nums font-semibold">{s.gap_score}</TD>
                      <TD className="tabular-nums">{s.open_positions}</TD>
                      <TD>
                        <Badge variant={s.gap_score > 20 ? "destructive" : s.gap_score > 8 ? "warning" : "success"}>
                          {s.gap_score > 20 ? "High" : s.gap_score > 8 ? "Medium" : "Balanced"}
                        </Badge>
                      </TD>
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
