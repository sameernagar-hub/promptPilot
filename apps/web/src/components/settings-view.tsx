"use client";

import { Database, Settings } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { getHealth } from "@/lib/api";

type Health = Awaited<ReturnType<typeof getHealth>>;

export function SettingsView() {
  const [health, setHealth] = useState<Health | null>(null);
  const [status, setStatus] = useState("Loading");

  useEffect(() => {
    getHealth()
      .then((value) => {
        setHealth(value);
        setStatus(value.status);
      })
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <main className="min-h-screen bg-[#f6f7f2] text-[#1d2523]">
      <header className="border-b border-[#d9ded2] bg-[#fbfcf7]">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-md bg-[#1e4d45] text-white">
              <Settings className="size-4" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">Settings</h1>
              <p className="text-xs text-[#65736f]">API {status}</p>
            </div>
          </div>
          <nav className="flex items-center gap-2 text-sm">
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/">
              Workspace
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/profile">
              Profile
            </Link>
          </nav>
        </div>
      </header>

      <section className="mx-auto grid max-w-5xl gap-4 px-4 py-4 md:grid-cols-2">
        <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
          <div className="mb-3 flex items-center gap-2">
            <Database className="size-4 text-[#1e4d45]" />
            <h2 className="text-sm font-semibold">Runtime</h2>
          </div>
          <dl className="space-y-2 text-sm">
            <SettingRow label="Service" value={health?.service ?? "promptpilot-api"} />
            <SettingRow label="Database" value={health?.database.database ?? "prompt_engine"} />
            <SettingRow label="Provider" value={health?.model_provider ?? "ollama"} />
            <SettingRow label="Model" value={health?.default_model ?? "ollama/llama3.1:8b"} />
          </dl>
        </div>

        <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold">Default Tuner Values</h2>
          <dl className="space-y-2 text-sm">
            <SettingRow label="Length" value="medium" />
            <SettingRow label="Skill" value="practical" />
            <SettingRow label="Tone" value="friendly" />
            <SettingRow label="Format" value="guide" />
            <SettingRow label="Risk" value="normal" />
            <SettingRow label="Sources" value="none" />
          </dl>
        </div>
      </section>
    </main>
  );
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-[#eef1ec] py-2 last:border-0">
      <dt className="text-[#65736f]">{label}</dt>
      <dd className="truncate font-medium">{value}</dd>
    </div>
  );
}
