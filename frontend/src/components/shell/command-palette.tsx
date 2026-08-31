"use client";

import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Search } from "lucide-react";

import { NAV } from "./nav";
import { useAuth } from "@/lib/auth";

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") {
        if (e.key === "/" && ["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) return;
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const items = NAV.filter((i) => !i.roles || (user && i.roles.includes(user.role)));

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex h-9 w-full max-w-xs items-center gap-2 rounded-md border border-input bg-card px-3 text-sm text-muted-foreground transition-colors hover:border-primary"
      >
        <Search className="size-4" />
        <span className="hidden sm:inline">Search & navigate</span>
        <kbd className="ml-auto hidden rounded border border-border px-1.5 text-[10px] sm:inline">⌘K</kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-[100] flex items-start justify-center bg-black/40 p-4 pt-[15vh]" onClick={() => setOpen(false)}>
          <div className="w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
            <Command className="overflow-hidden rounded-xl border border-border bg-popover shadow-2xl" loop>
              <div className="flex items-center gap-2 border-b border-border px-3">
                <Search className="size-4 text-muted-foreground" />
                <Command.Input autoFocus placeholder="Jump to a section…" className="h-11 w-full bg-transparent text-sm outline-none" />
              </div>
              <Command.List className="max-h-80 overflow-y-auto p-2">
                <Command.Empty className="px-3 py-6 text-center text-sm text-muted-foreground">No results.</Command.Empty>
                {items.map((item) => (
                  <Command.Item
                    key={item.href}
                    value={item.label}
                    onSelect={() => {
                      router.push(item.href);
                      setOpen(false);
                    }}
                    className="flex cursor-pointer items-center gap-2.5 rounded-md px-3 py-2 text-sm aria-selected:bg-secondary"
                  >
                    <item.icon className="size-4 text-muted-foreground" />
                    {item.label}
                    <span className="ml-auto text-xs text-muted-foreground">{item.group}</span>
                  </Command.Item>
                ))}
              </Command.List>
            </Command>
          </div>
        </div>
      )}
    </>
  );
}
