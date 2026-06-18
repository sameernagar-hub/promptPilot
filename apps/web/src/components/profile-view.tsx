"use client";

import {
  Brain,
  Check,
  Database,
  Gauge,
  HelpCircle,
  History,
  Library,
  Lightbulb,
  MessageSquare,
  Pencil,
  RefreshCw,
  Send,
  Sparkles,
  Target,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import Link from "next/link";
import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

import {
  askProfileQuestion,
  correctProfileObservation,
  deleteProfileObservation,
  getProfile,
  getProfileInsights,
  ProfileEvidenceReference,
  ProfileInsightItem,
  ProfileInsights,
  ProfileQuestionResponse,
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
  const [insights, setInsights] = useState<ProfileInsights | null>(null);
  const [answer, setAnswer] = useState<ProfileQuestionResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [status, setStatus] = useState("Loading");
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [asking, setAsking] = useState(false);
  const [editingTraitId, setEditingTraitId] = useState<string | null>(null);
  const [correctionSummary, setCorrectionSummary] = useState("");
  const [correctionNote, setCorrectionNote] = useState("");
  const [correctionScore, setCorrectionScore] = useState(50);
  const [busyTraitId, setBusyTraitId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void Promise.all([getProfile(), getProfileInsights()])
      .then(([profileValue, insightsValue]) => {
        if (!active) {
          return;
        }
        setProfile(profileValue);
        setInsights(insightsValue);
        setStatus(profileValue.status);
      })
      .catch((caught: unknown) => {
        if (!active) {
          return;
        }
        setError(caught instanceof Error ? caught.message : "Profile unavailable");
        setStatus("Offline");
      });
    return () => {
      active = false;
    };
  }, []);

  async function refresh() {
    setRefreshing(true);
    setError("");
    try {
      const profileValue = await refreshProfile();
      const insightsValue = await getProfileInsights();
      setProfile(profileValue);
      setInsights(insightsValue);
      setStatus(profileValue.status);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

  async function submitQuestion(event?: FormEvent<HTMLFormElement>, prompt?: string) {
    event?.preventDefault();
    const nextQuestion = (prompt ?? question).trim();
    if (!nextQuestion) {
      setError("Ask a profile question first");
      return;
    }
    setAsking(true);
    setError("");
    try {
      const response = await askProfileQuestion(nextQuestion);
      setAnswer(response);
      setQuestion(nextQuestion);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Profile answer failed");
    } finally {
      setAsking(false);
    }
  }

  function beginCorrection(trait: TraitObservation) {
    setEditingTraitId(trait.id);
    setCorrectionSummary(trait.summary);
    setCorrectionNote(trait.user_note ?? "");
    setCorrectionScore(Math.round(trait.score * 100));
  }

  async function saveCorrection(trait: TraitObservation) {
    setBusyTraitId(trait.id);
    setError("");
    try {
      const updated = await correctProfileObservation(trait.id, {
        summary: correctionSummary.trim(),
        score: correctionScore / 100,
        note: correctionNote.trim() || null,
      });
      setProfile(updated);
      setInsights(await getProfileInsights());
      setEditingTraitId(null);
      setStatus("Corrected");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Correction failed");
    } finally {
      setBusyTraitId(null);
    }
  }

  async function hideObservation(trait: TraitObservation) {
    setBusyTraitId(trait.id);
    setError("");
    try {
      await deleteProfileObservation(trait.id);
      setProfile((current) =>
        current
          ? {
              ...current,
              traits: current.traits.filter((item) => item.id !== trait.id),
              observation_count: Math.max(current.observation_count - 1, 0),
            }
          : current,
      );
      setInsights(await getProfileInsights());
      setStatus("Observation hidden");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Delete failed");
    } finally {
      setBusyTraitId(null);
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
          <nav className="grid w-full grid-cols-2 items-center gap-2 text-sm sm:flex sm:w-auto sm:flex-wrap">
            <Link className="rounded-md px-2 py-1 text-center hover:bg-[#edf1e8]" href="/">
              Workspace
            </Link>
            <Link className="rounded-md px-2 py-1 text-center hover:bg-[#edf1e8]" href="/library">
              Library
            </Link>
            <Link className="rounded-md px-2 py-1 text-center hover:bg-[#edf1e8]" href="/profile/imports">
              Imports
            </Link>
            <Link className="rounded-md px-2 py-1 text-center hover:bg-[#edf1e8]" href="/settings">
              Settings
            </Link>
            <Button
              className="col-span-2 w-full sm:w-auto"
              type="button"
              variant="outline"
              onClick={refresh}
              disabled={refreshing}
            >
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

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
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
            value={profile?.traits.length ?? profile?.observation_count ?? 0}
          />
          <MetricCard
            icon={<Sparkles className="size-4" />}
            label="Signals"
            value={profile?.summary.signal_count ?? 0}
          />
        </section>

        <section className="mt-4 rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <h2 className="text-sm font-semibold">{profile?.display_name ?? "Local profile"}</h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-[#65736f]">
                {insights?.headline ??
                  profile?.summary.headline ??
                  "Profile evidence is not available yet."}
              </p>
              {insights?.empty_state ? (
                <p className="mt-2 text-sm leading-6 text-[#865c12]">
                  {insights.empty_state}
                </p>
              ) : null}
            </div>
            <div className="shrink-0 rounded-md bg-[#edf1e8] px-2 py-1 text-xs font-medium text-[#34413e]">
              {profile?.last_refreshed_at
                ? new Date(profile.last_refreshed_at).toLocaleString()
                : "Not refreshed"}
            </div>
          </div>
        </section>

        <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <section className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <HelpCircle className="size-4 text-[#1e4d45]" />
              <h2 className="text-sm font-semibold">Ask Your Profile</h2>
            </div>
            <form className="space-y-3" onSubmit={submitQuestion}>
              <textarea
                className="min-h-28 w-full resize-y rounded-md border border-[#cbd5cd] bg-white p-3 text-sm leading-6 outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="What do I usually forget to include?"
              />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-xs text-[#65736f]">
                  {answer ? `${formatPercent(answer.confidence)} confidence` : "Grounded in profile evidence"}
                </div>
                <Button type="submit" disabled={asking}>
                  <Send />
                  {asking ? "Answering" : "Ask"}
                </Button>
              </div>
            </form>
            {insights?.suggested_questions.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {insights.suggested_questions.slice(0, 4).map((suggestion) => (
                  <Button
                    key={suggestion}
                    className="h-auto min-h-7 max-w-full whitespace-normal text-left"
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => submitQuestion(undefined, suggestion)}
                    disabled={asking}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            ) : null}
            {answer ? <AnswerPanel answer={answer} /> : null}
          </section>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
            <InsightSection
              icon={<Lightbulb className="size-4" />}
              title="Common Missing Details"
              items={insights?.common_missing_details ?? []}
            />
            <InsightSection
              icon={<Target className="size-4" />}
              title="Preferences"
              items={insights?.preferences ?? []}
            />
          </section>
        </div>

        <section className="mt-4 grid gap-4 lg:grid-cols-3">
          <InsightSection
            icon={<Library className="size-4" />}
            title="Frequent Domains"
            items={insights?.frequent_domains ?? []}
          />
          <InsightSection
            icon={<Brain className="size-4" />}
            title="Platform Advice"
            items={insights?.platform_advice ?? []}
          />
          <InsightSection
            icon={<History className="size-4" />}
            title="Recent Revisions"
            items={insights?.recent_revisions ?? []}
            emptyText="No prompt revisions yet."
          />
        </section>

        {profile && profile.traits.length ? (
          <div className="mt-4 space-y-4">
            {groupedTraits.map(([category, traits]) => (
              <section key={category}>
                <h2 className="mb-2 text-sm font-semibold">
                  {categoryLabels[category] ?? humanize(category)}
                </h2>
                <div className="grid gap-3 lg:grid-cols-2">
                  {traits.map((trait) => (
                    <TraitCard
                      key={trait.id}
                      trait={trait}
                      editing={editingTraitId === trait.id}
                      busy={busyTraitId === trait.id}
                      correctionSummary={correctionSummary}
                      correctionNote={correctionNote}
                      correctionScore={correctionScore}
                      onEdit={() => beginCorrection(trait)}
                      onCancel={() => setEditingTraitId(null)}
                      onSummaryChange={setCorrectionSummary}
                      onNoteChange={setCorrectionNote}
                      onScoreChange={setCorrectionScore}
                      onSave={() => saveCorrection(trait)}
                      onDelete={() => hideObservation(trait)}
                    />
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
            <Link
              href="/profile/imports"
              className="inline-flex items-center gap-2 rounded-md text-[#1e4d45] hover:underline"
            >
              <UploadCloud className="size-4" />
              Add chat imports
            </Link>
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
  icon: ReactNode;
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

function InsightSection({
  icon,
  title,
  items,
  emptyText = "No insight available yet.",
}: {
  icon: ReactNode;
  title: string;
  items: ProfileInsightItem[];
  emptyText?: string;
}) {
  return (
    <section className="rounded-md border border-[#d9ded2] bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-[#eef1ec] px-4 py-3">
        <span className="text-[#1e4d45]">{icon}</span>
        <h2 className="text-sm font-semibold">{title}</h2>
      </div>
      <div className="divide-y divide-[#eef1ec]">
        {items.length ? (
          items
            .slice(0, 5)
            .map((item, index) => (
              <InsightCard key={`${title}-${item.title}-${index}`} item={item} />
            ))
        ) : (
          <p className="px-4 py-5 text-sm text-[#65736f]">{emptyText}</p>
        )}
      </div>
    </section>
  );
}

function InsightCard({ item }: { item: ProfileInsightItem }) {
  return (
    <article className="px-4 py-3">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <h3 className="min-w-0 text-sm font-semibold">{item.title}</h3>
        <span className="rounded-md bg-[#e9f2f6] px-2 py-1 text-[11px] font-medium text-[#295061]">
          {formatPercent(item.confidence)}
        </span>
      </div>
      <p className="text-sm leading-6 text-[#34413e]">{item.detail}</p>
      {item.action ? (
        <p className="mt-2 text-xs leading-5 text-[#65736f]">{item.action}</p>
      ) : null}
      {item.evidence.length ? (
        <div className="mt-2 space-y-2">
          {item.evidence.slice(0, 2).map((evidence, index) => (
            <EvidenceReferenceItem key={`${item.title}-${index}`} evidence={evidence} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function AnswerPanel({ answer }: { answer: ProfileQuestionResponse }) {
  return (
    <section className="mt-4 border-t border-[#eef1ec] pt-4">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">{answer.question}</h3>
        <span className={cn("rounded-md px-2 py-1 text-[11px] font-medium", answerClass(answer.evidence_level))}>
          {answer.evidence_level}
        </span>
      </div>
      <p className="text-sm leading-6 text-[#34413e]">{answer.answer}</p>
      {answer.evidence.length ? (
        <div className="mt-3 space-y-2">
          {answer.evidence.map((evidence, index) => (
            <EvidenceReferenceItem key={`${answer.question}-${index}`} evidence={evidence} />
          ))}
        </div>
      ) : null}
      {answer.suggested_followups.length ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {answer.suggested_followups.map((followup) => (
            <span
              key={followup}
              className="rounded-md bg-[#edf1e8] px-2 py-1 text-xs text-[#34413e]"
            >
              {followup}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function TraitCard({
  trait,
  editing,
  busy,
  correctionSummary,
  correctionNote,
  correctionScore,
  onEdit,
  onCancel,
  onSummaryChange,
  onNoteChange,
  onScoreChange,
  onSave,
  onDelete,
}: {
  trait: TraitObservation;
  editing: boolean;
  busy: boolean;
  correctionSummary: string;
  correctionNote: string;
  correctionScore: number;
  onEdit: () => void;
  onCancel: () => void;
  onSummaryChange: (value: string) => void;
  onNoteChange: (value: string) => void;
  onScoreChange: (value: number) => void;
  onSave: () => void;
  onDelete: () => void;
}) {
  return (
    <article className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{trait.trait_label}</h3>
            {trait.user_corrected ? (
              <span className="rounded-md bg-[#e9f2f6] px-2 py-1 text-[11px] font-medium text-[#295061]">
                corrected
              </span>
            ) : null}
          </div>
          <p className="text-xs text-[#65736f]">{humanize(trait.trait_key)}</p>
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
      {trait.user_note ? (
        <p className="mt-2 border-l-2 border-[#3c7a89] pl-3 text-xs leading-5 text-[#295061]">
          {trait.user_note}
        </p>
      ) : null}

      {editing ? (
        <CorrectionPanel
          summary={correctionSummary}
          note={correctionNote}
          score={correctionScore}
          busy={busy}
          onSummaryChange={onSummaryChange}
          onNoteChange={onNoteChange}
          onScoreChange={onScoreChange}
          onSave={onSave}
          onCancel={onCancel}
        />
      ) : (
        <div className="mt-3 flex flex-wrap gap-2 border-t border-[#eef1ec] pt-3">
          <Button type="button" variant="outline" size="sm" onClick={onEdit} disabled={busy}>
            <Pencil />
            Correct
          </Button>
          <Button type="button" variant="destructive" size="sm" onClick={onDelete} disabled={busy}>
            <Trash2 />
            Hide
          </Button>
        </div>
      )}

      {trait.signals.length ? (
        <div className="mt-3 space-y-2 border-t border-[#eef1ec] pt-3">
          {trait.signals.slice(0, 2).map((signal) => (
            <SignalItem key={signal.id} signal={signal} />
          ))}
        </div>
      ) : null}
      {trait.evidence.length ? (
        <div className="mt-3 space-y-2">
          {trait.evidence.slice(0, 2).map((item, index) => (
            <TraitEvidenceItem key={`${trait.id}-${item.session_id ?? index}`} item={item} />
          ))}
        </div>
      ) : null}
    </article>
  );
}

function CorrectionPanel({
  summary,
  note,
  score,
  busy,
  onSummaryChange,
  onNoteChange,
  onScoreChange,
  onSave,
  onCancel,
}: {
  summary: string;
  note: string;
  score: number;
  busy: boolean;
  onSummaryChange: (value: string) => void;
  onNoteChange: (value: string) => void;
  onScoreChange: (value: number) => void;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="mt-3 space-y-3 border-t border-[#eef1ec] pt-3">
      <label className="block space-y-1 text-xs font-medium text-[#34413e]">
        <span>Corrected summary</span>
        <textarea
          className="min-h-24 w-full resize-y rounded-md border border-[#cbd5cd] bg-white p-3 text-sm leading-6 outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
          value={summary}
          onChange={(event) => onSummaryChange(event.target.value)}
        />
      </label>
      <label className="block space-y-2 text-xs font-medium text-[#34413e]">
        <span>Score: {score}</span>
        <input
          className="w-full accent-[#1e4d45]"
          type="range"
          min={0}
          max={100}
          value={score}
          onChange={(event) => onScoreChange(Number(event.target.value))}
        />
      </label>
      <label className="block space-y-1 text-xs font-medium text-[#34413e]">
        <span>Note</span>
        <input
          className="h-9 w-full rounded-md border border-[#cbd5cd] bg-white px-2 text-sm outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
          value={note}
          onChange={(event) => onNoteChange(event.target.value)}
          placeholder="Why this correction is better"
        />
      </label>
      <div className="flex flex-wrap gap-2">
        <Button type="button" size="sm" onClick={onSave} disabled={busy}>
          <Check />
          Save
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={onCancel} disabled={busy}>
          <X />
          Cancel
        </Button>
      </div>
    </div>
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

function answerClass(level: string) {
  if (level === "strong") {
    return "bg-[#1e4d45] text-white";
  }
  if (level === "emerging") {
    return "bg-[#dbebe0] text-[#214b40]";
  }
  if (level === "tentative") {
    return "bg-amber-100 text-amber-800";
  }
  return "bg-[#edf1e8] text-[#65736f]";
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
    <div className="border-l-2 border-[#d9ded2] pl-3 text-xs leading-5">
      <div className="mb-1 flex items-center justify-between gap-3">
        <span className="font-medium text-[#34413e]">{signal.signal_label}</span>
        <span className="text-[#1e4d45]">{Math.round(signal.score * 100)}</span>
      </div>
      <p className="text-[#65736f]">{signal.explanation}</p>
    </div>
  );
}

function TraitEvidenceItem({
  item,
}: {
  item: TraitObservation["evidence"][number];
}) {
  const content = (
    <div className="border-l-2 border-[#e9f2f6] pl-3 text-xs leading-5 text-[#34413e]">
      <div className="mb-1 flex flex-wrap items-center gap-2 text-[#65736f]">
        <Library className="size-3" />
        {item.domain ? humanize(item.domain) : "session"}
        {item.intent ? <span>{humanize(item.intent)}</span> : null}
      </div>
      <p className="break-words">{item.excerpt}</p>
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

function EvidenceReferenceItem({ evidence }: { evidence: ProfileEvidenceReference }) {
  const content = (
    <div className="border-l-2 border-[#d9ded2] pl-3 text-xs leading-5 text-[#34413e]">
      <div className="mb-1 flex flex-wrap items-center gap-2 text-[#65736f]">
        <Library className="size-3" />
        <span>{evidence.label}</span>
        {evidence.confidence != null ? <span>{formatPercent(evidence.confidence)}</span> : null}
      </div>
      {evidence.excerpt ? <p className="break-words">{evidence.excerpt}</p> : null}
    </div>
  );

  if (evidence.session_id) {
    return (
      <Link href={`/sessions/${evidence.session_id}`} className="block hover:opacity-85">
        {content}
      </Link>
    );
  }
  return content;
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function humanize(value: string) {
  return value.replaceAll("_", " ");
}
