"use client";

import { Bell, CheckCheck } from "lucide-react";

import { PageHeader } from "@/components/shell/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge, EmptyState, Skeleton } from "@/components/ui/misc";
import { useMarkAllRead, useMarkNotificationRead, useNotifications } from "@/lib/hooks";
import { cn, relativeTime } from "@/lib/utils";

const TONE: Record<string, "default" | "success" | "warning" | "destructive"> = {
  info: "default",
  success: "success",
  warning: "warning",
  alert: "destructive",
};

export default function NotificationsPage() {
  const { data, isLoading } = useNotifications({ page_size: 50 });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllRead();

  return (
    <div className="space-y-5">
      <PageHeader
        title="Notifications"
        description="Programme alerts, workflow updates and broadcasts."
        actions={
          <Button variant="outline" onClick={() => markAll.mutate()} loading={markAll.isPending}>
            <CheckCheck className="size-4" /> Mark all read
          </Button>
        }
      />
      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}</div>
      ) : !data?.items.length ? (
        <EmptyState icon={Bell} title="You're all caught up" />
      ) : (
        <div className="space-y-2">
          {data.items.map((n) => (
            <Card
              key={n.id}
              className={cn("flex items-start gap-3 p-4", !n.is_read && "border-l-4 border-l-primary")}
              onClick={() => !n.is_read && markRead.mutate(n.id)}
            >
              <Badge variant={TONE[n.type]}>{n.type}</Badge>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold">{n.title}</p>
                {n.body && <p className="mt-0.5 text-sm text-muted-foreground">{n.body}</p>}
                <p className="mt-1 text-xs text-muted-foreground">{relativeTime(n.created_at)}</p>
              </div>
              {!n.is_read && <span className="mt-1.5 size-2 shrink-0 rounded-full bg-primary" />}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
