"use client";

import { useState } from "react";
import { Building2, MapPin, Users } from "lucide-react";

import { PageHeader } from "@/components/shell/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge, EmptyState, NativeSelect, Progress, Skeleton } from "@/components/ui/misc";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDistricts, usePrograms, useProviders, useSectors } from "@/lib/hooks";
import { formatCurrency, titleCase } from "@/lib/utils";

export default function TrainingPage() {
  const [q, setQ] = useState("");
  const [district, setDistrict] = useState("");
  const [sector, setSector] = useState("");
  const { data: districts } = useDistricts();
  const { data: sectors } = useSectors();
  const { data: programs, isLoading } = usePrograms({ q: q || undefined, district: district || undefined, sector: sector || undefined });
  const { data: providers } = useProviders();

  return (
    <div className="space-y-5">
      <PageHeader
        title="Training Programs"
        description="NSQF-aligned training batches, providers, seats, eligibility and schedule. DEMO/SIMULATED catalogue."
      />

      <Card>
        <CardContent className="flex flex-wrap gap-2 py-4">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search program…" className="max-w-xs" />
          <NativeSelect value={district} onChange={(e) => setDistrict(e.target.value)}>
            <option value="">All districts</option>
            {districts?.map((d) => <option key={d} value={d}>{d}</option>)}
          </NativeSelect>
          <NativeSelect value={sector} onChange={(e) => setSector(e.target.value)}>
            <option value="">All sectors</option>
            {sectors?.map((s) => <option key={s} value={s}>{s}</option>)}
          </NativeSelect>
        </CardContent>
      </Card>

      <Tabs defaultValue="programs">
        <TabsList>
          <TabsTrigger value="programs">Programs ({programs?.meta.total ?? 0})</TabsTrigger>
          <TabsTrigger value="providers">Providers ({providers?.meta.total ?? 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="programs">
          {isLoading ? (
            <div className="grid gap-3 md:grid-cols-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-40 w-full" />)}</div>
          ) : !programs?.items.length ? (
            <EmptyState icon={Building2} title="No programs match" />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {programs.items.map((p) => {
                const fill = p.total_seats ? (p.filled_seats / p.total_seats) * 100 : 0;
                return (
                  <Card key={p.id} className="p-4">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-display text-sm font-semibold">{p.title}</h3>
                      <StatusBadge status={p.status} />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {p.skill?.name} · NSQF L{p.nsqf_level} · {titleCase(p.mode)} · {p.duration_weeks}w / {p.duration_hours}h
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1.5 text-xs">
                      <Badge variant="secondary"><MapPin className="mr-1 size-3" />{p.location?.district ?? "—"}</Badge>
                      <Badge variant="secondary">{p.provider?.name}</Badge>
                      {p.fee === 0 && <Badge variant="success">PM-AJAY funded</Badge>}
                      {p.stipend_monthly > 0 && <Badge variant="default">Stipend {formatCurrency(p.stipend_monthly)}</Badge>}
                    </div>
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span><Users className="mr-1 inline size-3" />{p.filled_seats}/{p.total_seats} seats</span>
                        <span>{p.seats_available} available</span>
                      </div>
                      <Progress value={fill} className="mt-1" indicatorClassName={fill > 90 ? "bg-destructive" : ""} />
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Eligibility: {titleCase(p.eligibility_min_education)}+ · age {p.eligibility_min_age}–{p.eligibility_max_age ?? "∞"}
                    </p>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="providers">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {providers?.items.map((pr: any) => (
              <Card key={pr.id} className="p-4">
                <h3 className="font-display text-sm font-semibold">{pr.name}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{titleCase(pr.type)} · {pr.accreditation} · ★ {pr.rating}</p>
                <p className="mt-2 text-xs text-muted-foreground">{pr.location?.district}, {pr.location?.state}</p>
                <p className="text-xs text-muted-foreground">{pr.contact_email}</p>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
