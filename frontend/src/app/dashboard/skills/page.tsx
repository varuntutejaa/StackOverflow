"use client";

import { useState } from "react";
import { BookMarked } from "lucide-react";

import { PageHeader } from "@/components/shell/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge, EmptyState, NativeSelect, Skeleton } from "@/components/ui/misc";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useRoles, useSectors, useSkills } from "@/lib/hooks";
import type { NsqfRole, Skill } from "@/lib/types";
import { formatCurrency, titleCase } from "@/lib/utils";

export default function NsqfCataloguePage() {
  const [sector, setSector] = useState("");
  const [level, setLevel] = useState("");
  const [q, setQ] = useState("");
  const { data: sectors } = useSectors();
  const { data: skills, isLoading } = useSkills({ sector: sector || undefined, nsqf_level: level || undefined, q: q || undefined });
  const { data: roles } = useRoles({ sector: sector || undefined });
  const [detail, setDetail] = useState<Skill | null>(null);
  const [roleDetail, setRoleDetail] = useState<NsqfRole | null>(null);

  return (
    <div className="space-y-5">
      <PageHeader
        title="NSQF Skill Catalogue"
        description="NSQF-aligned skills and job roles with eligibility, duration, sector, QP codes and required competencies. All entries are DEMO/SIMULATED."
      />

      <Card>
        <CardContent className="flex flex-wrap gap-2 py-4">
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search skill / role…" className="max-w-xs" />
          <NativeSelect value={sector} onChange={(e) => setSector(e.target.value)}>
            <option value="">All sectors</option>
            {sectors?.map((s) => <option key={s} value={s}>{s}</option>)}
          </NativeSelect>
          <NativeSelect value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="">All NSQF levels</option>
            {[2, 3, 4, 5, 6].map((l) => <option key={l} value={l}>Level {l}</option>)}
          </NativeSelect>
        </CardContent>
      </Card>

      <Tabs defaultValue="skills">
        <TabsList>
          <TabsTrigger value="skills">Skills ({skills?.meta.total ?? 0})</TabsTrigger>
          <TabsTrigger value="roles">Job Roles ({roles?.meta.total ?? 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="skills">
          <Card className="p-0">
            {isLoading ? (
              <div className="space-y-2 p-4">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
            ) : !skills?.items.length ? (
              <div className="p-6"><EmptyState icon={BookMarked} title="No skills match" /></div>
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Skill</TH>
                    <TH>Sector</TH>
                    <TH>NSQF</TH>
                    <TH>Min education</TH>
                    <TH>Duration</TH>
                    <TH>Avg wage</TH>
                    <TH>Demand</TH>
                  </TR>
                </THead>
                <TBody>
                  {skills.items.map((s) => (
                    <TR key={s.id} className="cursor-pointer" onClick={() => setDetail(s)}>
                      <TD>
                        <span className="font-medium">{s.name}</span>
                        {s.self_employable && <Badge variant="success" className="ml-2">Self-employable</Badge>}
                        <div className="text-xs text-muted-foreground">{s.code}</div>
                      </TD>
                      <TD className="text-muted-foreground">{s.sector}</TD>
                      <TD>L{s.nsqf_level}</TD>
                      <TD>{titleCase(s.min_education)}</TD>
                      <TD className="tabular-nums">{s.typical_duration_hours}h</TD>
                      <TD className="tabular-nums">{s.avg_wage_monthly ? formatCurrency(s.avg_wage_monthly) : "—"}</TD>
                      <TD className="tabular-nums">{s.demand_index.toFixed(0)}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="roles">
          <div className="grid gap-3 md:grid-cols-2">
            {roles?.items.map((r) => (
              <Card key={r.id} className="cursor-pointer p-4 transition-colors hover:border-primary" onClick={() => setRoleDetail(r)}>
                <div className="flex items-center justify-between">
                  <h3 className="font-display font-semibold">{r.title}</h3>
                  <Badge variant={r.growth_outlook === "high" || r.growth_outlook === "growing" ? "success" : "secondary"}>
                    {titleCase(r.growth_outlook)}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {r.sector} · NSQF L{r.nsqf_level} · NCO {r.nco_code} · QP {r.qp_code}
                </p>
                <p className="mt-2 text-sm">{r.description}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Entry wage {r.entry_wage_monthly ? formatCurrency(r.entry_wage_monthly) : "—"} · {r.skills.length} linked skills
                </p>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={!!detail} onOpenChange={(o) => !o && setDetail(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader><DialogTitle>{detail?.name}</DialogTitle></DialogHeader>
          {detail && (
            <div className="space-y-3 text-sm">
              <p className="text-muted-foreground">{detail.description}</p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  ["Sector", detail.sector],
                  ["NSQF Level", `L${detail.nsqf_level}`],
                  ["Min education", titleCase(detail.min_education)],
                  ["Age band", `${detail.min_age}–${detail.max_age ?? "∞"}`],
                  ["Duration", `${detail.typical_duration_hours} hrs`],
                  ["Avg wage", detail.avg_wage_monthly ? formatCurrency(detail.avg_wage_monthly) + "/mo" : "—"],
                ].map(([k, v]) => (
                  <div key={k as string} className="flex justify-between border-b border-border pb-1">
                    <span className="text-muted-foreground">{k}</span>
                    <span className="font-medium">{v as string}</span>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">Prerequisites</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {detail.prerequisites.length ? detail.prerequisites.map((p) => <Badge key={p} variant="secondary">{p}</Badge>) : <span className="text-xs text-muted-foreground">None</span>}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">Tags</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {detail.tags.map((p) => <Badge key={p} variant="default">{p}</Badge>)}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={!!roleDetail} onOpenChange={(o) => !o && setRoleDetail(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader><DialogTitle>{roleDetail?.title}</DialogTitle></DialogHeader>
          {roleDetail && (
            <div className="space-y-3 text-sm">
              <p className="text-muted-foreground">{roleDetail.description}</p>
              <p><span className="font-semibold">Eligibility:</span> {roleDetail.eligibility}</p>
              <p><span className="font-semibold">Self-employment path:</span> {roleDetail.self_employment_path}</p>
              <div>
                <p className="text-xs font-semibold uppercase text-muted-foreground">Required skills</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {roleDetail.skills.map((s) => <Badge key={s.id} variant="secondary">{s.name}</Badge>)}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
