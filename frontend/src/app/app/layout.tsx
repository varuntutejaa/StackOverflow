"use client";

import Link from "next/link";

import { Logo } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

export default function BeneficiaryLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen bg-background">
      <div className="h-1 w-full gov-stripe" />
      <header className="container flex items-center justify-between py-3">
        <Link href="/">
          <Logo />
        </Link>
        <div className="flex items-center gap-2 text-sm">
          {user ? (
            <>
              <span className="hidden text-muted-foreground sm:inline">{user.full_name}</span>
              {user.role !== "beneficiary" && (
                <Button asChild variant="ghost" size="sm">
                  <Link href="/dashboard">Admin portal</Link>
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={() => logout()}>
                Sign out
              </Button>
            </>
          ) : (
            <Button asChild size="sm">
              <Link href="/login">Sign in</Link>
            </Button>
          )}
        </div>
      </header>
      <main className="container max-w-3xl py-6">{children}</main>
    </div>
  );
}
