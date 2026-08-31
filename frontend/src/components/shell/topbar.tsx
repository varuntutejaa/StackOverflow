"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { Bell, LogOut, Menu, Moon, Sun, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown";
import { Badge } from "@/components/ui/misc";
import { useAuth } from "@/lib/auth";
import { useHealth, useUnreadCount } from "@/lib/hooks";
import { initials, titleCase } from "@/lib/utils";

import { CommandPalette } from "./command-palette";

export function Topbar({ onMenu }: { onMenu: () => void }) {
  const { user, logout } = useAuth();
  const { data: unread } = useUnreadCount();
  const { data: health } = useHealth();
  const { theme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-card/80 px-4 backdrop-blur sm:px-6">
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenu} aria-label="Open menu">
        <Menu className="size-5" />
      </Button>

      <CommandPalette />

      <div className="ml-auto flex items-center gap-1.5">
        {health?.ai?.mock_mode && (
          <Badge variant="warning" className="hidden md:inline-flex">
            AI: mock providers
          </Badge>
        )}
        <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Toggle theme">
          <Sun className="size-4 dark:hidden" />
          <Moon className="hidden size-4 dark:block" />
        </Button>

        <Button asChild variant="ghost" size="icon" className="relative" aria-label="Notifications">
          <Link href="/dashboard/notifications">
            <Bell className="size-4" />
            {!!unread?.unread && (
              <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
                {unread.unread}
              </span>
            )}
          </Link>
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-full border border-border bg-card py-1 pl-1 pr-3 transition-colors hover:bg-secondary">
              <span className="grid size-7 place-items-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                {user ? initials(user.full_name) : "?"}
              </span>
              <span className="hidden text-left sm:block">
                <span className="block text-xs font-semibold leading-tight">{user?.full_name}</span>
                <span className="block text-[10px] leading-tight text-muted-foreground">
                  {user ? titleCase(user.role) : ""}
                </span>
              </span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/dashboard/settings">
                <UserRound className="size-4" /> Profile & settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => logout()} className="text-destructive">
              <LogOut className="size-4" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
