"use client";

import { useMemo, useState } from "react";

import type { MapPoint } from "@/lib/types";
import { cn } from "@/lib/utils";

// Approx bounding box of Jharkhand
const BOUNDS = { minLat: 21.9, maxLat: 25.5, minLng: 83.3, maxLng: 88.1 };
const W = 620;
const H = 520;

function project(lat: number, lng: number) {
  const x = ((lng - BOUNDS.minLng) / (BOUNDS.maxLng - BOUNDS.minLng)) * W;
  const y = H - ((lat - BOUNDS.minLat) / (BOUNDS.maxLat - BOUNDS.minLat)) * H;
  return { x, y };
}

type Metric = "beneficiaries" | "avg_gap_score" | "training_centers" | "open_opportunities" | "placed";

const METRICS: { key: Metric; label: string }[] = [
  { key: "beneficiaries", label: "Beneficiaries" },
  { key: "avg_gap_score", label: "Skill gap" },
  { key: "training_centers", label: "Training centres" },
  { key: "open_opportunities", label: "Opportunities" },
  { key: "placed", label: "Placed" },
];

export function LivelihoodMap({ points }: { points: MapPoint[] }) {
  const [metric, setMetric] = useState<Metric>("beneficiaries");
  const [hover, setHover] = useState<MapPoint | null>(null);

  const max = useMemo(
    () => Math.max(1, ...points.map((p) => Number(p[metric] ?? 0))),
    [points, metric],
  );

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-1.5">
        {METRICS.map((m) => (
          <button
            key={m.key}
            onClick={() => setMetric(m.key)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              metric === m.key ? "border-primary bg-primary/10 text-primary" : "border-border text-muted-foreground hover:bg-secondary",
            )}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="relative overflow-hidden rounded-lg border border-border bg-[radial-gradient(circle_at_30%_20%,hsl(var(--secondary))_0%,hsl(var(--card))_70%)]">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full">
          <rect width={W} height={H} fill="transparent" />
          {points
            .filter((p) => p.latitude && p.longitude)
            .map((p) => {
              const { x, y } = project(p.latitude!, p.longitude!);
              const v = Number(p[metric] ?? 0);
              const r = 8 + (v / max) * 34;
              const active = hover?.location_id === p.location_id;
              return (
                <g
                  key={p.location_id}
                  onMouseEnter={() => setHover(p)}
                  onMouseLeave={() => setHover(null)}
                  className="cursor-pointer"
                >
                  <circle cx={x} cy={y} r={r} className={cn("transition-all", active ? "fill-accent/40" : "fill-primary/25")} />
                  <circle cx={x} cy={y} r={4} className={active ? "fill-accent" : "fill-primary"} />
                  <text x={x} y={y - r - 4} textAnchor="middle" className="fill-foreground text-[9px] font-medium">
                    {p.district}
                  </text>
                </g>
              );
            })}
        </svg>

        {hover && (
          <div className="pointer-events-none absolute right-3 top-3 w-56 rounded-lg border border-border bg-popover p-3 text-xs shadow-lg">
            <p className="font-display text-sm font-semibold">{hover.district}</p>
            <p className="text-muted-foreground">{hover.state}</p>
            <dl className="mt-2 space-y-1">
              <Row k="Beneficiaries" v={hover.beneficiaries} />
              <Row k="Interviews done" v={hover.interviews_done} />
              <Row k="In training" v={hover.in_training} />
              <Row k="Certified" v={hover.certified} />
              <Row k="Placed / self-emp" v={hover.placed} />
              <Row k="Training centres" v={hover.training_centers} />
              <Row k="Open opportunities" v={hover.open_opportunities} />
              <Row k="Avg demand / supply" v={`${hover.avg_demand_score} / ${hover.avg_supply_score}`} />
              <Row k="Avg skill gap" v={hover.avg_gap_score} />
            </dl>
            {hover.top_gap_skills.length > 0 && (
              <p className="mt-2 text-muted-foreground">
                Top gaps: <span className="text-foreground">{hover.top_gap_skills.join(", ")}</span>
              </p>
            )}
          </div>
        )}
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Bubble size = {METRICS.find((m) => m.key === metric)?.label}. Positions approximate district centroids (Jharkhand). DEMO/SIMULATED.
      </p>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="font-medium">{v}</dd>
    </div>
  );
}
