import { Badge } from "@/components/ui/misc";
import { titleCase } from "@/lib/utils";

const MAP: Record<string, "default" | "secondary" | "success" | "warning" | "destructive"> = {
  registered: "secondary",
  interview_pending: "warning",
  interview_done: "default",
  recommended: "default",
  in_training: "warning",
  certified: "success",
  placed: "success",
  self_employed: "success",
  dropped_out: "destructive",
  archived: "secondary",
  // interview
  created: "secondary",
  in_progress: "warning",
  completed: "success",
  abandoned: "destructive",
  // application
  draft: "secondary",
  submitted: "default",
  under_review: "warning",
  waitlisted: "warning",
  accepted: "default",
  rejected: "destructive",
  enrolled: "warning",
  withdrawn: "destructive",
  // training program
  upcoming: "secondary",
  open: "success",
  ongoing: "warning",
  cancelled: "destructive",
};

export function StatusBadge({ status }: { status: string }) {
  return <Badge variant={MAP[status] ?? "secondary"}>{titleCase(status)}</Badge>;
}
