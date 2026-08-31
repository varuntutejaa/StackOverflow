"use client";

import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { BriefcaseBusiness, Crosshair, GraduationCap, MapPin } from "lucide-react";
import { useMemo, useState } from "react";
import { CircleMarker, MapContainer, Marker, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import type { MapPoint } from "@/lib/types";
import { cn } from "@/lib/utils";

type Metric = "beneficiaries" | "avg_gap_score" | "training_centers" | "open_opportunities" | "placed";

const MANIPAL_JAIPUR = {
  lat: 26.8425,
  lng: 75.5654,
  label: "Manipal University Jaipur / Bagru",
};

const METRICS: { key: Metric; label: string }[] = [
  { key: "beneficiaries", label: "Beneficiaries" },
  { key: "avg_gap_score", label: "Skill gap" },
  { key: "training_centers", label: "Training centres" },
  { key: "open_opportunities", label: "Opportunities" },
  { key: "placed", label: "Placed" },
];

const LOCAL_OPPORTUNITIES = [
  {
    id: "bagru-textile-printing",
    kind: "opportunity",
    title: "Bagru Textile Printing Cluster",
    detail: "Block printing, dyeing assistant, finishing and packaging roles",
    skill: "Textile Printing & Apparel",
    seats: 42,
    lat: 26.8053,
    lng: 75.5411,
  },
  {
    id: "mahindra-sez-solar",
    kind: "opportunity",
    title: "Mahindra World City Jaipur",
    detail: "Solar maintenance, warehouse operations and electrical helper openings",
    skill: "Solar PV / Electrical",
    seats: 31,
    lat: 26.7909,
    lng: 75.8246,
  },
  {
    id: "ajmer-road-retail",
    kind: "opportunity",
    title: "Ajmer Road Service Corridor",
    detail: "Customer support, retail operations and delivery supervisor pathways",
    skill: "Retail & Logistics",
    seats: 24,
    lat: 26.8578,
    lng: 75.6468,
  },
  {
    id: "bagru-industrial-area",
    kind: "opportunity",
    title: "Bagru Industrial Area",
    detail: "Machine operator, packaging, quality-check and helper roles",
    skill: "Manufacturing Operations",
    seats: 38,
    lat: 26.8118,
    lng: 75.5158,
  },
  {
    id: "muj-training-hub",
    kind: "training",
    title: "MUJ Community Skilling Hub",
    detail: "Digital literacy, spoken English, solar basics and placement readiness",
    skill: "Foundation / Digital",
    seats: 60,
    lat: 26.8439,
    lng: 75.5647,
  },
  {
    id: "bagru-iti-linkage",
    kind: "training",
    title: "Bagru ITI Linkage Centre",
    detail: "Electrician assistant, tailoring, welding and workshop safety batches",
    skill: "NSQF Level 3-4",
    seats: 50,
    lat: 26.8096,
    lng: 75.5449,
  },
] as const;

function makeDivIcon(kind: "home" | "training" | "opportunity") {
  const classes = {
    home: "bg-primary text-primary-foreground ring-primary/25",
    training: "bg-success text-success-foreground ring-success/25",
    opportunity: "bg-accent text-accent-foreground ring-accent/25",
  }[kind];
  const glyph = kind === "home" ? "MUJ" : kind === "training" ? "T" : "O";

  return L.divIcon({
    className: "",
    html: `<div class="grid h-8 w-8 place-items-center rounded-full ${classes} text-[10px] font-bold shadow-lg ring-4">${glyph}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
}

function Recenter({ center }: { center: [number, number] }) {
  const map = useMap();
  map.setView(center, map.getZoom(), { animate: true });
  return null;
}

export function LivelihoodMap({ points }: { points: MapPoint[] }) {
  const [metric, setMetric] = useState<Metric>("beneficiaries");
  const [center, setCenter] = useState<[number, number]>([MANIPAL_JAIPUR.lat, MANIPAL_JAIPUR.lng]);

  const districtPoints = useMemo(
    () => points.filter((p) => typeof p.latitude === "number" && typeof p.longitude === "number"),
    [points],
  );
  const max = useMemo(
    () => Math.max(1, ...districtPoints.map((p) => Number(p[metric] ?? 0))),
    [districtPoints, metric],
  );

  function useMyLocation() {
    if (!navigator.geolocation) {
      toast.error("Location is not available in this browser");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCenter([pos.coords.latitude, pos.coords.longitude]);
        toast.success("Map centered on your current location");
      },
      () => toast.error("Location permission was not granted"),
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60_000 },
    );
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1.5">
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
        <Button type="button" size="sm" variant="outline" onClick={useMyLocation}>
          <Crosshair className="size-4" />
          Use my location
        </Button>
      </div>

      <div className="relative overflow-hidden rounded-lg border border-border">
        <MapContainer center={center} zoom={10} scrollWheelZoom className="h-[520px] w-full">
          <Recenter center={center} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <Marker position={[MANIPAL_JAIPUR.lat, MANIPAL_JAIPUR.lng]} icon={makeDivIcon("home")}>
            <Popup>
              <div className="space-y-1">
                <p className="font-semibold">{MANIPAL_JAIPUR.label}</p>
                <p className="text-xs">Local anchor for nearby livelihood opportunities.</p>
              </div>
            </Popup>
          </Marker>

          {LOCAL_OPPORTUNITIES.map((item) => (
            <Marker key={item.id} position={[item.lat, item.lng]} icon={makeDivIcon(item.kind)}>
              <Popup>
                <div className="max-w-56 space-y-1">
                  <p className="font-semibold">{item.title}</p>
                  <p className="text-xs">{item.detail}</p>
                  <p className="text-xs">
                    <b>Skill:</b> {item.skill}
                  </p>
                  <p className="text-xs">
                    <b>Open seats/roles:</b> {item.seats}
                  </p>
                </div>
              </Popup>
              <Tooltip direction="top">{item.title}</Tooltip>
            </Marker>
          ))}

          {districtPoints.map((p) => {
            const v = Number(p[metric] ?? 0);
            const radius = 8 + (v / max) * 24;
            return (
              <CircleMarker
                key={p.location_id}
                center={[p.latitude!, p.longitude!]}
                radius={radius}
                pathOptions={{
                  color: "hsl(var(--primary))",
                  fillColor: "hsl(var(--primary))",
                  fillOpacity: 0.22,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="min-w-56 space-y-2">
                    <div>
                      <p className="font-semibold">{p.district}</p>
                      <p className="text-xs text-slate-500">{p.state}</p>
                    </div>
                    <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                      <Row k="Beneficiaries" v={p.beneficiaries} />
                      <Row k="Interviews" v={p.interviews_done} />
                      <Row k="In training" v={p.in_training} />
                      <Row k="Certified" v={p.certified} />
                      <Row k="Placed" v={p.placed} />
                      <Row k="Centres" v={p.training_centers} />
                      <Row k="Opportunities" v={p.open_opportunities} />
                      <Row k="Gap" v={p.avg_gap_score} />
                    </dl>
                    {p.top_gap_skills.length > 0 && (
                      <p className="text-xs">
                        <b>Top gaps:</b> {p.top_gap_skills.join(", ")}
                      </p>
                    )}
                  </div>
                </Popup>
                <Tooltip direction="top">{p.district}</Tooltip>
              </CircleMarker>
            );
          })}
        </MapContainer>

        <div className="absolute bottom-3 left-3 z-[400] rounded-md border border-border bg-popover/95 p-2 text-xs shadow-lg backdrop-blur">
          <div className="flex items-center gap-2">
            <MapPin className="size-3.5 text-primary" /> MUJ / Bagru anchor
          </div>
          <div className="mt-1 flex items-center gap-2">
            <BriefcaseBusiness className="size-3.5 text-accent" /> Nearby opportunities
          </div>
          <div className="mt-1 flex items-center gap-2">
            <GraduationCap className="size-3.5 text-success" /> Training hubs
          </div>
        </div>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        OpenStreetMap base map with DEMO/SIMULATED livelihood overlays. Local markers are placed around Manipal University Jaipur, Bagru and Ajmer Road.
      </p>
    </div>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <>
      <dt className="text-slate-500">{k}</dt>
      <dd className="text-right font-medium">{v}</dd>
    </>
  );
}
