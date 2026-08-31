"use client";

import Link from "next/link";
import { useState } from "react";
import { Download, Plus, Search, Users } from "lucide-react";

import { PageHeader } from "@/components/shell/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { EmptyState, NativeSelect, Skeleton } from "@/components/ui/misc";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { API_BASE, tokenStore } from "@/lib/api";
import { useBeneficiaries, useDistricts } from "@/lib/hooks";
import { titleCase } from "@/lib/utils";

const STATUSES = ["registered", "interview_pending", "interview_done", "recommended", "in_training", "certified", "placed", "self_employed", "archived"];
const EDU = ["none", "primary", "middle", "secondary", "senior_secondary", "iti", "diploma", "graduate"];
const LANGS = [
  ["hi", "Hindi"],
  ["en", "English"],
  ["sat", "Santhali"],
  ["hoc", "Ho"],
  ["unr", "Mundari"],
];

export default function BeneficiariesPage() {
  const [page, setPage] = useState(1);
  const [q, setQ] = useState("");
  const [filters, setFilters] = useState({ district: "", status: "", education_level: "", language: "", occupation: "" });
  const { data: districts } = useDistricts();
  const { data, isLoading } = useBeneficiaries({ page, page_size: 15, q: q || undefined, ...clean(filters) });

  function clean(f: Record<string, string>) {
    return Object.fromEntries(Object.entries(f).filter(([, v]) => v));
  }

  async function exportCsv() {
    const res = await fetch(`${API_BASE}/beneficiaries/export/csv?${new URLSearchParams(clean(filters))}`, {
      headers: { authorization: `Bearer ${tokenStore.access}` },
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "beneficiaries.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const items = data?.items ?? [];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Beneficiaries"
        description="Register, interview, recommend and track SC beneficiaries under PM-AJAY."
        actions={
          <>
            <Button variant="outline" onClick={exportCsv}>
              <Download className="size-4" /> Export CSV
            </Button>
            <Button asChild>
              <Link href="/dashboard/beneficiaries/new">
                <Plus className="size-4" /> New beneficiary
              </Link>
            </Button>
          </>
        }
      />

      <Card>
        <CardContent className="flex flex-wrap gap-2 py-4">
          <div className="relative min-w-[200px] flex-1">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} placeholder="Search name, phone, PM-AJAY ID…" className="pl-9" />
          </div>
          <NativeSelect value={filters.district} onChange={(e) => setFilters((f) => ({ ...f, district: e.target.value }))}>
            <option value="">All districts</option>
            {districts?.map((d) => <option key={d} value={d}>{d}</option>)}
          </NativeSelect>
          <NativeSelect value={filters.status} onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}>
            <option value="">Any status</option>
            {STATUSES.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
          </NativeSelect>
          <NativeSelect value={filters.education_level} onChange={(e) => setFilters((f) => ({ ...f, education_level: e.target.value }))}>
            <option value="">Any education</option>
            {EDU.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
          </NativeSelect>
          <NativeSelect value={filters.language} onChange={(e) => setFilters((f) => ({ ...f, language: e.target.value }))}>
            <option value="">Any language</option>
            {LANGS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </NativeSelect>
        </CardContent>
      </Card>

      <Card className="p-0">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : items.length === 0 ? (
          <div className="p-6">
            <EmptyState icon={Users} title="No beneficiaries match" description="Adjust filters or register a new beneficiary." />
          </div>
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Name</TH>
                <TH>District / Village</TH>
                <TH>Age</TH>
                <TH>Education</TH>
                <TH>Occupation</TH>
                <TH>Language</TH>
                <TH>Status</TH>
              </TR>
            </THead>
            <TBody>
              {items.map((b) => (
                <TR key={b.id} className="cursor-pointer">
                  <TD>
                    <Link href={`/dashboard/beneficiaries/${b.id}`} className="font-medium hover:text-primary">
                      {b.full_name}
                    </Link>
                    {b.is_demo && <span className="ml-2 text-[10px] font-semibold text-accent">DEMO</span>}
                  </TD>
                  <TD className="text-muted-foreground">
                    {b.district || "—"} {b.village ? `· ${b.village}` : ""}
                  </TD>
                  <TD className="tabular-nums">{b.age ?? "—"}</TD>
                  <TD>{titleCase(b.education_level)}</TD>
                  <TD className="text-muted-foreground">{b.current_occupation ? titleCase(b.current_occupation) : "—"}</TD>
                  <TD className="uppercase">{b.preferred_language}</TD>
                  <TD><StatusBadge status={b.status} /></TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      {data && data.meta.pages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Page {data.meta.page} of {data.meta.pages} · {data.meta.total} total
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={page >= data.meta.pages} onClick={() => setPage((p) => p + 1)}>
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
