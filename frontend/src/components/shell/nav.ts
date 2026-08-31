import {
  Bell,
  Blocks,
  BookMarked,
  Building2,
  GraduationCap,
  LayoutDashboard,
  LineChart,
  MapPinned,
  Mic,
  Settings,
  Sparkles,
  TrendingUp,
  Trophy,
  Users,
  Users2,
} from "lucide-react";

import type { Role } from "@/lib/types";

export interface NavItem {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  roles?: Role[];
  group: "Insights" | "Beneficiary Journey" | "Catalogue" | "Administration";
}

export const NAV: NavItem[] = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, group: "Insights" },
  { href: "/dashboard/map", label: "Livelihood Map", icon: MapPinned, group: "Insights" },
  { href: "/dashboard/skill-demand", label: "Skill Demand", icon: TrendingUp, group: "Insights" },
  { href: "/dashboard/outcomes", label: "Outcomes", icon: Trophy, group: "Insights" },
  { href: "/dashboard/reports", label: "Reports", icon: LineChart, group: "Insights" },

  { href: "/dashboard/beneficiaries", label: "Beneficiaries", icon: Users, group: "Beneficiary Journey" },
  { href: "/dashboard/interviews", label: "AI Interviews", icon: Mic, group: "Beneficiary Journey" },
  { href: "/dashboard/recommendations", label: "Recommendations", icon: Sparkles, group: "Beneficiary Journey" },
  { href: "/dashboard/applications", label: "Training Applications", icon: GraduationCap, group: "Beneficiary Journey" },

  { href: "/dashboard/skills", label: "NSQF Catalogue", icon: BookMarked, group: "Catalogue" },
  { href: "/dashboard/training", label: "Training Programs", icon: Building2, group: "Catalogue" },
  { href: "/dashboard/opportunities", label: "Opportunities", icon: Blocks, group: "Catalogue" },

  { href: "/dashboard/notifications", label: "Notifications", icon: Bell, group: "Administration" },
  { href: "/dashboard/users", label: "Users & Roles", icon: Users2, roles: ["admin"], group: "Administration" },
  { href: "/dashboard/settings", label: "Settings", icon: Settings, group: "Administration" },
];

export const NAV_GROUPS = ["Insights", "Beneficiary Journey", "Catalogue", "Administration"] as const;
