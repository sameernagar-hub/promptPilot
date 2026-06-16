"use client";

import {
  Brain,
  Database,
  Gauge,
  Library,
  MessageSquare,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  getProfile,
  PromptProfile,
  refreshProfile,
  TraitObservation,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const categoryLabels: Record<string, string> = {
  domain: "Domain",
  input_quality: "Input Quality",
  preferences: "Preferences",
  safety: "Safety",
  workflow: "Workflow",
  foundation: "Foundation",
};

export function ProfileView() {
  const [profile, setProfile] = useState<PromptProfile | null>(null);
  const [status, setStatus] = useState("Loading");
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    getProfile()
      .then((value) => {
        setProfile(value);
        setStatus(value.status);
      })
      .catch((caught: unknown) => {
        setError(caught instanceof Error ? caught.message : "Profile unavailable");
        setStatus("Offline");
      });
  }, []);

  async function refresh() {
    setRefreshing(true);
    setError("");
    try {
      const value = await refreshProfile();
      setProfile(value);
      setStatus(value.status);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

  const groupedTraits = useMemo(() => {
    const groups = new Map<string, TraitObservation[]>();
    for (const trait of profile?.traits ?? []) {
      const traits = groups.get(trait.category) ?? [];
      traits.push(trait);
      groups.set(trait.category, traits);
    }
    return Array.from(groups.entries()).sort(([left], [right]) =>
      left.localeCompare(right),
    );
  }, [profile?.traits]);

  return (
    <main className="min-h-screen bg-[#f6f7f2] text-[#1d2523]">
      <header className="border-b border-[#d9ded2] bg-[#fbfcf7]">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-md bg-[#1e4d45] text-white">
              <Brain className="size-4" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">Prompting Profile</h1>
              <p className="text-xs text-[#65736f]">{status}</p>
            </div>
          </div>
          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/">
              Workspace
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/library">
              Library
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/settings">
              Settings
            </Link>
            <Button type="button" variant="outline" onClick={refresh} disabled={refreshing}>
              <RefreshCw className={cn(refreshing ? "animate-spin" : "")} />
              Refresh
            </Button>
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 py-4">
        {error ? (
          <p className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
            {error}
          </p>
        ) : null}

        <section className="grid gap-3 md:grid-cols-4">
          <MetricCard
            icon={<MessageSquare className="size-4" />}
            label="Sessions"
            value={profile?.total_sessions ?? 0}
          />
          <MetricCard
            icon={<Database className="size-4" />}
            label="Imports"
            value={profile?.total_imports ?? 0}
          />
          <MetricCard
            icon={<Gauge className="size-4" />}
            label="Traits"
            value={profile?.observation_count ?? 0}
          />
          <MetricCard
            icon={<Sparkles className="size-4" />}
            label="Evidence"
            value={profile?.summary.needs_more_evidence ? "Growing" : "Ready"}
          />
        </section>

        <section className="mt-4 rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div>
              <h2 className="text-sm font-semibold">{profile?.display_name ?? "Local profile"}</h2>
              <p className="mt-1 text-sm text-[#65736f]">
                {profile?.summary.headline ?? "Profile evidence is not available yet."}
              </p>
            </div>
            <div className="rounded-md bg-[#edf1e8] px-2 py-1 text-xs font-medium text-[#34413e]">
              {profile?.last_refreshed_at
                ? new Date(profile.last_refreshed_at).toLocaleString()
                : "Not refreshed"}
            </div>
          </div>
        </section>

        {profile && profile.traits.length ? (
          <div className="mt-4 space-y-4">
            {groupedTraits.map(([category, traits]) => (
              <section key={category}>
                <h2 className="mb-2 text-sm font-semibold">
                  {categoryLabels[category] ?? category.replaceAll("_", " ")}
                </h2>
                <div className="grid gap-3 md:grid-cols-2">
                  {traits.map((trait) => (
                    <TraitCard key={trait.id} trait={trait} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        ) : (
          <section className="mt-4 rounded-md border border-dashed border-[#c8d2ca] bg-white p-8 text-sm text-[#65736f]">
            <div className="mb-2 flex items-center gap-2 font-medium text-[#1d2523]">
              <Brain className="size-4" />
              No profile observations yet
            </div>
            Local prompt sessions will appear here after profile refresh.
          </section>
        )}
      </div>
    </main>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
}) {
  return (
    <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2 text-[#1e4d45]">{icon}</div>
      <div className="text-2xl font-semibold">{value}</div>
      <div className="text-xs text-[#65736f]">{label}</div>
    </div>
  );
}

function TraitCard({ trait }: { trait: TraitObservation }) {
  return (
    <article className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{trait.trait_label}</h3>
          <p className="text-xs text-[#65736f]">{trait.trait_key.replaceAll("_", " ")}</p>
        </div>
          <div className="text-right">
            <div className="text-xl font-semibold text-[#1e4d45]">
              {Math.round(trait.score * 100)}
            </div>
            <div className="text-[11px] text-[#65736f]">
              {Math.round(trait.confidence * 100)} conf
            </div>
          </div>
        </div>
      <div className="mb-3 flex flex-wrap gap-2">
        <span className={cn("rounded-md px-2 py-1 text-[11px] font-medium", evidenceClass(trait.evidence_level))}>
          {trait.evidence_level}
        </span>
        <span className="rounded-md bg-[#edf1e8] px-2 py-1 text-[11px] text-[#65736f]">
          {trait.signal_count} signals
        </span>
      </div>
      <ScoreBar value={trait.score} />
      <p className="mt-3 text-sm leading-6 text-[#34413e]">{trait.summary}</p>
      {trait.signals.length ? (
        <div className="mt-3 space-y-2">
          {trait.signals.slice(0, 2).map((signal) => (
            <SignalItem key={signal.id} signal={signal} />
          ))}
        </div>
      ) : null}
      {trait.evidence.length ? (
        <div className="mt-3 space-y-2">
          {trait.evidence.slice(0, 2).map((item, index) => (
            <EvidenceItem key={`${trait.id}-${item.session_id ?? index}`} item={item} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function evidenceClass(level: TraitObservation["evidence_level"]) {
  return {
    none: "bg-[#edf1e8] text-[#65736f]",
    tentative: "bg-amber-100 text-amber-800",
    emerging: "bg-[#dbebe0] text-[#214b40]",
    strong: "bg-[#1e4d45] text-white",
  }[level];
}

function ScoreBar({ value }: { value: number }) {
  return (
    <div className="h-2 overflow-hidden rounded-full bg-[#dfe5dd]">
      <div
        className="h-full rounded-full bg-[#1e4d45]"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}

function SignalItem({
  signal,
}: {
  signal: TraitObservation["signals"][number];
}) {
  return (
    <div className="rounded-md border border-[#eef1ec] bg-white px-3 py-2 text-xs leading-5">
      <div className="mb-1 flex items-center justify-between gap-3">
        <span className="font-medium text-[#34413e]">{signal.signal_label}</span>
        <span className="text-[#1e4d45]">{Math.round(signal.score * 100)}</span>
      </div>
      <p className="text-[#65736f]">{signal.explanation}</p>
    </div>
  );
}

function EvidenceItem({
  item,
}: {
  item: TraitObservation["evidence"][number];
}) {
  const content = (
    <div className="rounded-md border border-[#eef1ec] bg-[#fbfcf7] px-3 py-2 text-xs leading-5 text-[#34413e]">
      <div className="mb-1 flex flex-wrap items-center gap-2 text-[#65736f]">
        <Library className="size-3" />
        {item.domain ? item.domain.replaceAll("_", " ") : "session"}
        {item.intent ? <span>{item.intent.replaceAll("_", " ")}</span> : null}
      </div>
      <p className="line-clamp-2">{item.excerpt}</p>
    </div>
  );

  if (item.session_id) {
    return (
      <Link href={`/sessions/${item.session_id}`} className="block hover:opacity-85">
        {content}
      </Link>
    );
  }
  return content;
}
