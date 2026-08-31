"use client";

import { useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge, Label } from "@/components/ui/misc";
import { ApiError, apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useConfig, useHealth } from "@/lib/hooks";
import { titleCase } from "@/lib/utils";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const { data: config } = useConfig();
  const { data: health } = useHealth();
  const [profile, setProfile] = useState({ full_name: user?.full_name ?? "", phone: user?.phone ?? "", organisation: user?.organisation ?? "", district: user?.district ?? "" });
  const [pw, setPw] = useState({ current_password: "", new_password: "" });

  async function saveProfile() {
    try {
      await apiFetch("/auth/me", { method: "PATCH", body: profile });
      await refreshUser();
      toast.success("Profile updated");
    } catch (e) {
      toast.error(e instanceof ApiError ? String(e.detail) : "Failed");
    }
  }

  async function changePassword() {
    try {
      await apiFetch("/auth/change-password", { method: "POST", body: pw });
      toast.success("Password changed");
      setPw({ current_password: "", new_password: "" });
    } catch (e) {
      toast.error(e instanceof ApiError ? String(e.detail) : "Failed");
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Settings" description="Profile, security and platform configuration." />

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Profile</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5"><Label>Full name</Label><Input value={profile.full_name} onChange={(e) => setProfile((p) => ({ ...p, full_name: e.target.value }))} /></div>
            <div className="space-y-1.5"><Label>Phone</Label><Input value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))} /></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5"><Label>Organisation</Label><Input value={profile.organisation} onChange={(e) => setProfile((p) => ({ ...p, organisation: e.target.value }))} /></div>
              <div className="space-y-1.5"><Label>District</Label><Input value={profile.district} onChange={(e) => setProfile((p) => ({ ...p, district: e.target.value }))} /></div>
            </div>
            <Button onClick={saveProfile}>Save profile</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Security</CardTitle><CardDescription>Change your password</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-1.5"><Label>Current password</Label><Input type="password" value={pw.current_password} onChange={(e) => setPw((p) => ({ ...p, current_password: e.target.value }))} /></div>
            <div className="space-y-1.5"><Label>New password</Label><Input type="password" value={pw.new_password} onChange={(e) => setPw((p) => ({ ...p, new_password: e.target.value }))} /></div>
            <Button onClick={changePassword} disabled={!pw.current_password || pw.new_password.length < 8}>Change password</Button>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Platform status</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
            <Stat label="Environment" value={config?.env ?? "—"} />
            <Stat label="Database" value={health?.database_engine ?? "—"} tone={health?.database === "ok" ? "success" : "destructive"} />
            <Stat label="Cache" value={health?.cache_backend ?? "—"} />
            <Stat label="Supabase" value={config?.supabase_configured ? "configured" : "not configured"} tone={config?.supabase_configured ? "success" : "warning"} />
            <Stat label="STT provider" value={config?.ai.stt ?? "—"} />
            <Stat label="LLM provider" value={config?.ai.llm ?? "—"} />
            <Stat label="TTS provider" value={config?.ai.tts ?? "—"} />
            <Stat label="Translation" value={config?.ai.translate ?? "—"} />
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Supported languages</CardTitle></CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {config?.languages.map((l) => (
              <Badge key={l.code} variant="secondary">{l.label} <span className="ml-1 opacity-60">{l.code}</span></Badge>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "success" | "warning" | "destructive" }) {
  return (
    <div className="rounded-lg border border-border p-3">
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className={`mt-1 font-medium ${tone === "success" ? "text-success" : tone === "destructive" ? "text-destructive" : tone === "warning" ? "text-warning" : ""}`}>
        {titleCase(value)}
      </p>
    </div>
  );
}
