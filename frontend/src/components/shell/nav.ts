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
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard, roles: ["admin", "gov_officer"], group: "Insights" },
  { href: "/dashboard/map", label: "Livelihood Map", icon: MapPinned, roles: ["admin", "gov_officer"], group: "Insights" },
  { href: "/dashboard/skill-demand", label: "Skill Demand", icon: TrendingUp, roles: ["admin", "gov_officer"], group: "Insights" },
  { href: "/dashboard/outcomes", label: "Outcomes", icon: Trophy, roles: ["admin", "gov_officer"], group: "Insights" },
  { href: "/dashboard/reports", label: "Reports", icon: LineChart, roles: ["admin", "gov_officer"], group: "Insights" },

  { href: "/dashboard/beneficiaries", label: "Beneficiaries", icon: Users, roles: ["admin", "gov_officer"], group: "Beneficiary Journey" },
  { href: "/dashboard/interviews", label: "AI Interviews", icon: Mic, roles: ["admin", "gov_officer"], group: "Beneficiary Journey" },
  { href: "/dashboard/recommendations", label: "Recommendations", icon: Sparkles, roles: ["admin", "gov_officer"], group: "Beneficiary Journey" },
  { href: "/dashboard/applications", label: "Training Applications", icon: GraduationCap, roles: ["admin", "gov_officer", "training_provider"], group: "Beneficiary Journey" },

  { href: "/dashboard/skills", label: "NSQF Catalogue", icon: BookMarked, roles: ["admin", "gov_officer", "training_provider"], group: "Catalogue" },
  { href: "/dashboard/training", label: "Training Programs", icon: Building2, roles: ["admin", "gov_officer", "training_provider"], group: "Catalogue" },
  { href: "/dashboard/opportunities", label: "Opportunities", icon: Blocks, roles: ["admin", "gov_officer", "training_provider"], group: "Catalogue" },

  { href: "/dashboard/notifications", label: "Notifications", icon: Bell, roles: ["admin", "gov_officer", "training_provider"], group: "Administration" },
  { href: "/dashboard/users", label: "Users & Roles", icon: Users2, roles: ["admin"], group: "Administration" },
  { href: "/dashboard/settings", label: "Settings", icon: Settings, roles: ["admin"], group: "Administration" },
];

export const NAV_GROUPS = ["Insights", "Beneficiary Journey", "Catalogue", "Administration"] as const;

export function canAccessNavItem(role: Role | undefined, item: NavItem) {
  return !!role && (!item.roles || item.roles.includes(role));
}

export function firstDashboardPathForRole(role: Role) {
  return NAV.find((item) => canAccessNavItem(role, item))?.href ?? "/app/assistant";
}

export function canAccessDashboardPath(role: Role, pathname: string) {
  const item = NAV.filter((entry) => entry.href === pathname || (entry.href !== "/dashboard" && pathname.startsWith(`${entry.href}/`)))
    .sort((a, b) => b.href.length - a.href.length)[0];
  return item ? canAccessNavItem(role, item) : role === "admin";
}
