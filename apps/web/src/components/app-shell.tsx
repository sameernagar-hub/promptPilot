"use client";

import { Sparkles } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type AppShellProps = {
  title: string;
  status?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  maxWidth?: "5xl" | "6xl";
  children: ReactNode;
};

const maxWidthClass = {
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
};

export function AppShell({
  title,
  status,
  icon,
  actions,
  maxWidth = "6xl",
  children,
}: AppShellProps) {
  const width = maxWidthClass[maxWidth];

  return (
    <main className="min-h-screen bg-[#f6f7f2] text-[#1d2523]">
      <header className="border-b border-[#d9ded2] bg-[#fbfcf7]">
        <div className={cn("mx-auto flex items-center justify-between gap-3 px-4 py-3", width)}>
          <div className="flex min-w-0 items-center gap-3">
            <Link
              href="/"
              className="flex size-9 shrink-0 items-center justify-center rounded-md bg-[#1e4d45] text-white"
              title="PromptPilot home"
            >
              {icon ?? <Sparkles className="size-4" />}
            </Link>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold">{title}</h1>
              {status ? <p className="truncate text-xs text-[#65736f]">{status}</p> : null}
            </div>
          </div>
          <nav className="flex flex-wrap items-center justify-end gap-2 text-sm">
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/">
              Workspace
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/profile">
              Profile
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/profile/imports">
              Imports
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/library">
              Library
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/settings">
              Settings
            </Link>
            {actions}
          </nav>
        </div>
      </header>

      {children}

      <footer className="border-t border-[#d9ded2] bg-[#fbfcf7]">
        <div className={cn("mx-auto flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-xs text-[#65736f]", width)}>
          <span>PromptPilot</span>
          <span>Local-first prompt refinement, scoring, and profile controls.</span>
        </div>
      </footer>
    </main>
  );
}
