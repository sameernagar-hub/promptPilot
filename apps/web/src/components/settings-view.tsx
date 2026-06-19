"use client";

import { Database, Settings } from "lucide-react";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
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
    <AppShell
      title="Settings"
      status={`API ${status}`}
      icon={<Settings className="size-4" />}
      maxWidth="5xl"
    >
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
    </AppShell>
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
