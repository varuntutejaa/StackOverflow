"use client";

import { Download, FileSpreadsheet } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/misc";
import { API_BASE, tokenStore } from "@/lib/api";
import { useOutcomeDashboard, useOverview } from "@/lib/hooks";

function downloadJSON(name: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const { data: overview, isLoading } = useOverview();
  const { data: outcomes } = useOutcomeDashboard();

  async function exportBeneficiaryCsv() {
    const res = await fetch(`${API_BASE}/beneficiaries/export/csv`, {
      headers: { authorization: `Bearer ${tokenStore.access}` },
    });
    if (!res.ok) return toast.error("Export failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "beneficiaries.csv";
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Beneficiary register exported");
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Reports" description="Programme MIS extracts for review committees and PM-AJAY reporting." />

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Beneficiary register</CardTitle>
            <CardDescription>Full beneficiary list with status, skills and outcomes (CSV).</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={exportBeneficiaryCsv}><FileSpreadsheet className="size-4" /> Download CSV</Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Programme overview snapshot</CardTitle>
            <CardDescription>KPIs, funnel, district stats & skill demand (JSON).</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => downloadJSON("kaushai-overview.json", overview)} disabled={!overview}>
              <Download className="size-4" /> Download JSON
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Outcome dashboard</CardTitle>
            <CardDescription>Completion, placement, income improvement, district performance (JSON).</CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="outline" onClick={() => downloadJSON("kaushai-outcomes.json", outcomes)} disabled={!outcomes}>
              <Download className="size-4" /> Download JSON
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>District performance summary</CardTitle></CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b">
                  <tr className="text-left text-xs uppercase text-muted-foreground">
                    <th className="py-2">District</th><th>Beneficiaries</th><th>Interviews</th><th>Recommendations</th>
                    <th>In training</th><th>Certified</th><th>Placed</th><th>Self-employed</th><th>Placement %</th>
                  </tr>
                </thead>
                <tbody>
                  {overview?.district_stats.map((d) => (
                    <tr key={d.district} className="border-b last:border-0">
                      <td className="py-2 font-medium">{d.district}</td>
                      <td>{d.beneficiaries}</td><td>{d.interviews_done}</td><td>{d.recommendations}</td>
                      <td>{d.in_training}</td><td>{d.certified}</td><td>{d.placed}</td><td>{d.self_employed}</td>
                      <td>{d.placement_rate}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
