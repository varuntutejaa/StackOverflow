import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/misc";
import { formatNumber, formatPct } from "@/lib/utils";

export function KpiCard({
  label,
  value,
  unit,
  delta,
  hint,
}: {
  label: string;
  value: number;
  unit?: string;
  delta?: number | null;
  hint?: string;
}) {
  const display = unit === "percent" ? formatPct(value) : formatNumber(value);
  return (
    <Card className="p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <div className="mt-1.5 flex items-baseline gap-2">
        <span className="font-display text-2xl font-bold tabular-nums">{display}</span>
        {delta !== undefined && delta !== null && (
          <span className={`inline-flex items-center text-xs font-medium ${delta >= 0 ? "text-success" : "text-destructive"}`}>
            {delta >= 0 ? <ArrowUpRight className="size-3" /> : <ArrowDownRight className="size-3" />}
            {Math.abs(delta).toFixed(1)}%
          </span>
        )}
      </div>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </Card>
  );
}

export function KpiSkeleton() {
  return (
    <Card className="p-4">
      <Skeleton className="h-3 w-24" />
      <Skeleton className="mt-3 h-7 w-16" />
    </Card>
  );
}
