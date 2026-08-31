"use client";

import { useState } from "react";
import { Blocks } from "lucide-react";

import { PageHeader } from "@/components/shell/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge, EmptyState, NativeSelect, Skeleton } from "@/components/ui/misc";
import { useDistricts, useOpportunities, useSectors } from "@/lib/hooks";
import { formatCurrency, titleCase } from "@/lib/utils";

export default function OpportunitiesPage() {
  const [q, setQ] = useState("");
  const [district, setDistrict] = useState("");
  const [kind, setKind] = useState("");
  const { data: districts } = useDistricts();
  const { data: sectors } = useSectors();
  const { data, isLoading } = useOpportunities({ q: q || undefined, district: district || undefined, kind: kind || undefined });

  return (
    <div className="space-y-5">
      <PageHeader
        title="Livelihood Opportunities"
        description="Local wage jobs, apprenticeships and self-employment openings mapped to skills and districts. DEMO/SIMULATED signals."
      />
      <Card>
        <CardContent className="flex flex-wrap gap-2 py-4">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search…" className="max-w-xs" />
          <NativeSelect value={district} onChange={(e) => setDistrict(e.target.value)}>
            <option value="">All districts</option>
            {districts?.map((d) => <option key={d} value={d}>{d}</option>)}
          </NativeSelect>
          <NativeSelect value={kind} onChange={(e) => setKind(e.target.value)}>
            <option value="">All kinds</option>
            <option value="wage_job">Wage job</option>
            <option value="self_employment">Self-employment</option>
            <option value="apprenticeship">Apprenticeship</option>
          </NativeSelect>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>
      ) : !data?.items.length ? (
        <EmptyState icon={Blocks} title="No opportunities match" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {data.items.map((o: any) => (
            <Card key={o.id} className="p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-display text-sm font-semibold">{o.title}</h3>
                <Badge variant={o.kind === "self_employment" ? "success" : "default"}>{titleCase(o.kind)}</Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{o.sector} · {o.location?.district ?? "—"}</p>
              <p className="mt-2 text-sm">{o.employer ?? "Independent / SHG"}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {o.openings} opening(s) · {o.wage_monthly_min ? `${formatCurrency(o.wage_monthly_min)}–${formatCurrency(o.wage_monthly_max)}/mo` : "—"}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
