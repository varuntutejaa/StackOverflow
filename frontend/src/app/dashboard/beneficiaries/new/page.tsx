"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { Label, NativeSelect } from "@/components/ui/misc";
import { ApiError } from "@/lib/api";
import { useCreateBeneficiary, useLocations } from "@/lib/hooks";
import { titleCase } from "@/lib/utils";

const EDU = ["none", "primary", "middle", "secondary", "senior_secondary", "iti", "diploma", "graduate", "postgraduate"];
const LANGS = [["hi", "Hindi"], ["en", "English"], ["sat", "Santhali"], ["hoc", "Ho"], ["unr", "Mundari"]];
const MOBILITY = ["local", "district", "state", "anywhere"];
const PREF = ["any", "wage_employment", "self_employment", "apprenticeship"];
const GENDER = ["undisclosed", "male", "female", "other"];

export default function NewBeneficiaryPage() {
  const router = useRouter();
  const create = useCreateBeneficiary();
  const { data: locations } = useLocations();
  const [form, setForm] = useState<Record<string, any>>({
    full_name: "",
    age: "",
    gender: "undisclosed",
    phone: "",
    preferred_language: "hi",
    location_id: "",
    village: "",
    education_level: "secondary",
    current_occupation: "",
    family_occupation: "",
    monthly_income: "",
    skills: "",
    interests: "",
    constraints: "",
    mobility: "local",
    employment_preference: "any",
    has_smartphone: false,
    pmajay_id: "",
  });

  const set = (k: string, v: any) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const payload: Record<string, any> = {
      ...form,
      age: form.age ? Number(form.age) : null,
      monthly_income: form.monthly_income ? Number(form.monthly_income) : null,
      location_id: form.location_id || null,
      skills: splitList(form.skills),
      interests: splitList(form.interests),
      constraints: splitList(form.constraints),
    };
    Object.keys(payload).forEach((k) => (payload[k] === "" ) && delete payload[k]);
    try {
      const b = await create.mutateAsync(payload);
      toast.success("Beneficiary registered");
      router.push(`/dashboard/beneficiaries/${b.id}`);
    } catch (err) {
      toast.error(err instanceof ApiError ? String(err.detail) : "Could not create");
    }
  }

  function splitList(s: string) {
    return s.split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Register beneficiary" description="Create the record, then run the AI voice interview to build the profile." />
      <form onSubmit={submit} className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Identity</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Field label="Full name" className="sm:col-span-2">
              <Input required value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
            </Field>
            <Field label="Age"><Input type="number" min={10} max={100} value={form.age} onChange={(e) => set("age", e.target.value)} /></Field>
            <Field label="Gender">
              <NativeSelect className="w-full" value={form.gender} onChange={(e) => set("gender", e.target.value)}>
                {GENDER.map((g) => <option key={g} value={g}>{titleCase(g)}</option>)}
              </NativeSelect>
            </Field>
            <Field label="Phone"><Input value={form.phone} onChange={(e) => set("phone", e.target.value)} /></Field>
            <Field label="Preferred language">
              <NativeSelect className="w-full" value={form.preferred_language} onChange={(e) => set("preferred_language", e.target.value)}>
                {LANGS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </NativeSelect>
            </Field>
            <Field label="PM-AJAY ID" className="sm:col-span-2">
              <Input value={form.pmajay_id} onChange={(e) => set("pmajay_id", e.target.value)} placeholder="PMAJAY-JH-..." />
            </Field>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Location & work</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Field label="District (location)" className="sm:col-span-2">
              <NativeSelect className="w-full" value={form.location_id} onChange={(e) => set("location_id", e.target.value)}>
                <option value="">— select —</option>
                {locations?.items?.map((l: any) => (
                  <option key={l.id} value={l.id}>{l.district}, {l.state}</option>
                ))}
              </NativeSelect>
            </Field>
            <Field label="Village"><Input value={form.village} onChange={(e) => set("village", e.target.value)} /></Field>
            <Field label="Monthly income (₹)"><Input type="number" value={form.monthly_income} onChange={(e) => set("monthly_income", e.target.value)} /></Field>
            <Field label="Current occupation"><Input value={form.current_occupation} onChange={(e) => set("current_occupation", e.target.value)} /></Field>
            <Field label="Family / traditional occupation"><Input value={form.family_occupation} onChange={(e) => set("family_occupation", e.target.value)} /></Field>
            <Field label="Education">
              <NativeSelect className="w-full" value={form.education_level} onChange={(e) => set("education_level", e.target.value)}>
                {EDU.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
              </NativeSelect>
            </Field>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Aspirations & constraints</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Field label="Existing skills (comma separated)"><Input value={form.skills} onChange={(e) => set("skills", e.target.value)} placeholder="farming, electrical" /></Field>
            <Field label="Interests (comma separated)"><Input value={form.interests} onChange={(e) => set("interests", e.target.value)} placeholder="solar, electronics" /></Field>
            <Field label="Constraints (comma separated)"><Input value={form.constraints} onChange={(e) => set("constraints", e.target.value)} placeholder="financial, distance" /></Field>
            <Field label="Mobility">
              <NativeSelect className="w-full" value={form.mobility} onChange={(e) => set("mobility", e.target.value)}>
                {MOBILITY.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
              </NativeSelect>
            </Field>
            <Field label="Employment preference">
              <NativeSelect className="w-full" value={form.employment_preference} onChange={(e) => set("employment_preference", e.target.value)}>
                {PREF.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
              </NativeSelect>
            </Field>
            <label className="flex items-center gap-2 pt-6 text-sm">
              <input type="checkbox" checked={form.has_smartphone} onChange={(e) => set("has_smartphone", e.target.checked)} />
              Has a smartphone
            </label>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={() => router.back()}>Cancel</Button>
          <Button type="submit" loading={create.isPending}>Register beneficiary</Button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, children, className }: { label: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={`space-y-1.5 ${className ?? ""}`}>
      <Label>{label}</Label>
      {children}
    </div>
  );
}
