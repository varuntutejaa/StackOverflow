"use client";

import { useState } from "react";
import { GraduationCap } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shell/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge, EmptyState, Label, NativeSelect, Progress, Skeleton } from "@/components/ui/misc";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { ApiError } from "@/lib/api";
import { useApplicationAction, useApplications, useUpdateApplication } from "@/lib/hooks";
import type { Application } from "@/lib/types";
import { titleCase } from "@/lib/utils";

const NEXT_STATUS: Record<string, string[]> = {
  submitted: ["under_review", "accepted", "rejected"],
  under_review: ["accepted", "waitlisted", "rejected"],
  accepted: ["enrolled"],
  waitlisted: ["accepted", "rejected"],
  enrolled: ["in_progress", "withdrawn"],
  in_progress: ["completed", "withdrawn"],
  completed: ["certified"],
};

export default function ApplicationsPage() {
  const [status, setStatus] = useState("");
  const { data, isLoading, refetch } = useApplications({ page_size: 50, status: status || undefined });
  const update = useUpdateApplication();
  const action = useApplicationAction();
  const [certFor, setCertFor] = useState<Application | null>(null);
  const [score, setScore] = useState("75");

  async function transition(a: Application, to: string) {
    try {
      if (to === "enrolled") {
        await action.mutateAsync({ id: a.id, action: "enroll" });
      } else {
        await update.mutateAsync({ id: a.id, body: { status: to } });
      }
      toast.success(`Moved to ${titleCase(to)}`);
      refetch();
    } catch (e) {
      toast.error(e instanceof ApiError ? String(e.detail) : "Transition failed");
    }
  }

  async function issueCert() {
    if (!certFor) return;
    try {
      await action.mutateAsync({ id: certFor.id, action: "certificate", body: { assessment_score: Number(score) } });
      toast.success("Certificate processed");
      setCertFor(null);
      refetch();
    } catch (e) {
      toast.error(e instanceof ApiError ? String(e.detail) : "Failed");
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Training Applications"
        description="Application → eligibility → enrolment → progress → certification workflow."
        actions={
          <NativeSelect value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {["submitted", "under_review", "accepted", "enrolled", "in_progress", "completed", "certified", "rejected", "withdrawn"].map((s) => (
              <option key={s} value={s}>{titleCase(s)}</option>
            ))}
          </NativeSelect>
        }
      />

      <Card className="p-0">
        {isLoading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !data?.items.length ? (
          <div className="p-6"><EmptyState icon={GraduationCap} title="No applications" /></div>
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Program</TH>
                <TH>Eligibility</TH>
                <TH>Progress</TH>
                <TH>Status</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {data.items.map((a) => (
                <TR key={a.id}>
                  <TD className="max-w-[260px]">
                    <span className="font-medium">{a.program?.title ?? a.program_id}</span>
                    <div className="text-xs text-muted-foreground">{a.program?.provider?.name}</div>
                  </TD>
                  <TD>
                    <Badge variant={a.eligibility_passed ? "success" : "destructive"}>
                      {a.eligibility_passed ? "Passed" : "Failed"}
                    </Badge>
                  </TD>
                  <TD className="w-36"><Progress value={a.progress_pct} /></TD>
                  <TD><StatusBadge status={a.status} /></TD>
                  <TD>
                    <div className="flex flex-wrap gap-1.5">
                      {(NEXT_STATUS[a.status] ?? []).map((to) =>
                        to === "certified" ? (
                          <Button key={to} size="sm" variant="outline" onClick={() => setCertFor(a)}>
                            Issue certificate
                          </Button>
                        ) : (
                          <Button key={to} size="sm" variant="outline" onClick={() => transition(a, to)}>
                            {titleCase(to)}
                          </Button>
                        ),
                      )}
                    </div>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      <Dialog open={!!certFor} onOpenChange={(o) => !o && setCertFor(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Issue certificate</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Assessment score (0–100)</Label>
            <Input type="number" min={0} max={100} value={score} onChange={(e) => setScore(e.target.value)} />
            <p className="text-xs text-muted-foreground">Score ≥ 50 issues an NSQF certificate and marks the beneficiary certified.</p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCertFor(null)}>Cancel</Button>
            <Button onClick={issueCert} loading={action.isPending}>Confirm</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
