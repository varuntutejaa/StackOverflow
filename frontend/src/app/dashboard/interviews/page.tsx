"use client";

import Link from "next/link";
import { useState } from "react";
import { Mic } from "lucide-react";

import { PageHeader } from "@/components/shell/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Card } from "@/components/ui/card";
import { EmptyState, NativeSelect, Progress, Skeleton } from "@/components/ui/misc";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useInterviews } from "@/lib/hooks";
import { relativeTime, titleCase } from "@/lib/utils";

export default function InterviewsPage() {
  const [status, setStatus] = useState("");
  const { data, isLoading } = useInterviews({ page_size: 40, status: status || undefined });

  return (
    <div className="space-y-5">
      <PageHeader
        title="AI Interviews"
        description="Voice → STT → multilingual understanding → structured profile extraction sessions."
        actions={
          <NativeSelect value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="in_progress">In progress</option>
            <option value="completed">Completed</option>
            <option value="created">Created</option>
          </NativeSelect>
        }
      />
      <Card className="p-0">
        {isLoading ? (
          <div className="space-y-2 p-4">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : !data?.items.length ? (
          <div className="p-6"><EmptyState icon={Mic} title="No interviews" description="Start an interview from a beneficiary's profile." /></div>
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Interview</TH>
                <TH>Language</TH>
                <TH>Provider</TH>
                <TH>Progress</TH>
                <TH>Status</TH>
                <TH>Created</TH>
              </TR>
            </THead>
            <TBody>
              {data.items.map((iv) => (
                <TR key={iv.id}>
                  <TD>
                    <Link href={`/dashboard/beneficiaries/${iv.beneficiary_id}`} className="font-mono text-xs hover:text-primary">
                      {iv.id.slice(0, 8)}
                    </Link>
                  </TD>
                  <TD>{titleCase(iv.language)}</TD>
                  <TD className="text-muted-foreground">{iv.stt_provider}</TD>
                  <TD className="w-40">
                    <Progress value={iv.completion_pct} />
                  </TD>
                  <TD><StatusBadge status={iv.status} /></TD>
                  <TD className="text-muted-foreground">{relativeTime(iv.created_at)}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  );
}
