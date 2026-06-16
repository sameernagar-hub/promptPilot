"use client";

import {
  Check,
  Copy,
  GitCompare,
  Play,
  RefreshCw,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  createSession,
  defaultSettings,
  getHealth,
  getSession,
  PipelineResponse,
  PromptSettings,
  PromptVariant,
  runPipeline,
  runPrompt,
  savePrompt,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type WorkspaceProps = {
  initialSessionId?: string;
  initialCompare?: boolean;
};

const sampleProblems = [
  "My React app saves successfully but the UI stays stale after clicking save.",
  "I smell gas near my furnace and need a safe troubleshooting plan.",
  "I need to write a firm but respectful email to a client about a missed deadline.",
];

const timelineLabels: Record<string, string> = {
  classified: "Classified",
  questions_ready: "Questions",
  answers_recorded: "Answers",
  prompts_generated: "Generated",
  prompts_scored: "Scored",
  ready: "Ready",
};

const settingOptions = {
  length: ["short", "medium", "deep"],
  skill_level: ["beginner", "practical", "expert"],
  tone: ["direct", "friendly", "technical"],
  format: ["checklist", "guide", "table", "conversation", "plan"],
  risk: ["safe_only", "normal", "advanced"],
  sources: ["none", "web", "official_docs"],
} as const;

export function PromptWorkspace({
  initialSessionId,
  initialCompare = false,
}: WorkspaceProps) {
  const [problem, setProblem] = useState("");
  const [settings, setSettings] = useState<PromptSettings>(defaultSettings);
  const [sessionId, setSessionId] = useState<string | null>(
    initialSessionId ?? null,
  );
  const [sessionProblem, setSessionProblem] = useState("");
  const [pipeline, setPipeline] = useState<PipelineResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [runOutput, setRunOutput] = useState("");
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [compareMode, setCompareMode] = useState(initialCompare);
  const [apiHealth, setApiHealth] = useState<"ok" | "degraded" | "offline">(
    "offline",
  );

  useEffect(() => {
    getHealth()
      .then((health) => setApiHealth(health.status === "ok" ? "ok" : "degraded"))
      .catch(() => setApiHealth("offline"));
  }, []);

  useEffect(() => {
    if (!initialSessionId) {
      return;
    }
    getSession(initialSessionId)
      .then((session) => {
        setProblem(session.raw_input);
        setSessionProblem(session.raw_input);
        setSettings({ ...defaultSettings, ...session.user_settings });
        setAnswers(session.answers ?? {});
        setStatus(session.status);
      })
      .catch((caught: unknown) =>
        setError(caught instanceof Error ? caught.message : "Session not found"),
      );
  }, [initialSessionId]);

  const prompts = useMemo(() => pipeline?.prompts ?? [], [pipeline]);
  const selectedPrompt = useMemo(
    () =>
      prompts.find((prompt) => prompt.id === selectedPromptId) ??
      prompts.find((prompt) => prompt.id === pipeline?.recommended_prompt_id) ??
      prompts[0],
    [pipeline?.recommended_prompt_id, prompts, selectedPromptId],
  );

  async function generate() {
    if (!problem.trim()) {
      setError("Enter a problem before generating prompts.");
      return;
    }

    setLoading(true);
    setError("");
    setRunOutput("");
    try {
      const shouldCreateSession = !sessionId || problem.trim() !== sessionProblem;
      const session = shouldCreateSession
        ? await createSession(problem.trim(), settings)
        : { id: sessionId };
      if (shouldCreateSession) {
        setSessionId(session.id);
        setSessionProblem(problem.trim());
      }
      const result = await runPipeline(session.id, settings, answers);
      setPipeline(result);
      setSelectedPromptId(result.recommended_prompt_id);
      setStatus("Ready");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Generation failed");
      setStatus("Error");
    } finally {
      setLoading(false);
    }
  }

  async function runSelectedPrompt() {
    if (!sessionId || !selectedPrompt) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await runPrompt(sessionId, selectedPrompt.id);
      setRunOutput(result.output);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Run failed");
    } finally {
      setLoading(false);
    }
  }

  async function saveSelectedPrompt() {
    if (!selectedPrompt) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      await savePrompt(selectedPrompt.id, selectedPrompt.title);
      setStatus("Saved");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed");
    } finally {
      setLoading(false);
    }
  }

  async function copySelectedPrompt() {
    if (!selectedPrompt) {
      return;
    }
    await navigator.clipboard.writeText(selectedPrompt.prompt_text);
    setStatus("Copied");
  }

  const timeline = pipeline?.timeline ?? [];
  const healthClass =
    apiHealth === "ok"
      ? "bg-emerald-500"
      : apiHealth === "degraded"
        ? "bg-amber-500"
        : "bg-rose-500";

  return (
    <main className="min-h-screen bg-[#f6f7f2] text-[#1d2523]">
      <header className="border-b border-[#d9ded2] bg-[#fbfcf7]">
        <div className="mx-auto flex max-w-[1500px] flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-md bg-[#1e4d45] text-white">
              <Sparkles className="size-4" />
            </div>
            <div>
              <h1 className="text-lg font-semibold leading-tight">PromptPilot</h1>
              <p className="text-xs text-[#65736f]">
                {sessionId ? `Session ${sessionId.slice(0, 8)}` : "Workspace"}
              </p>
            </div>
          </div>
          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/">
              Workspace
            </Link>
            <Link
              className="rounded-md px-2 py-1 hover:bg-[#edf1e8]"
              href={sessionId ? `/compare/${sessionId}` : "/compare/new"}
            >
              Compare
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/library">
              Library
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/profile">
              Profile
            </Link>
            <Link className="rounded-md px-2 py-1 hover:bg-[#edf1e8]" href="/settings">
              Settings
            </Link>
            <span className="ml-1 inline-flex items-center gap-2 rounded-md border border-[#d9ded2] bg-white px-2 py-1 text-xs">
              <span className={cn("size-2 rounded-full", healthClass)} />
              API {apiHealth}
            </span>
          </nav>
        </div>
      </header>

      <div className="mx-auto grid max-w-[1500px] gap-4 px-4 py-4 xl:grid-cols-[minmax(280px,360px)_minmax(0,1fr)_minmax(280px,340px)]">
        <section className="space-y-4">
          <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">Problem</h2>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => {
                  setProblem(sampleProblems[Math.floor(Math.random() * sampleProblems.length)]);
                  setSessionId(null);
                  setSessionProblem("");
                  setPipeline(null);
                  setAnswers({});
                  setSelectedPromptId(null);
                }}
              >
                <RefreshCw />
                Sample
              </Button>
            </div>
            <textarea
              className="min-h-40 w-full resize-none rounded-md border border-[#ccd4ca] bg-[#fbfcf7] p-3 text-sm leading-6 outline-none ring-[#4f7f74]/20 focus:ring-4"
              value={problem}
              onChange={(event) => setProblem(event.target.value)}
              placeholder="Describe the problem to turn into a strong AI prompt."
            />
            <div className="mt-3 flex flex-wrap gap-2">
              <Button type="button" onClick={generate} disabled={loading}>
                <Sparkles />
                {loading ? "Generating" : "Generate"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={generate}
                disabled={loading || !sessionId}
              >
                <RefreshCw />
                Refresh
              </Button>
            </div>
            {error ? (
              <p className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
                {error}
              </p>
            ) : null}
          </div>

          <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <ShieldCheck className="size-4 text-[#1e4d45]" />
              <h2 className="text-sm font-semibold">Classification</h2>
            </div>
            {pipeline ? (
              <div className="grid gap-2 text-sm">
                <DomainBadge label={pipeline.classification.domain} />
                <MetaRow label="Intent" value={pipeline.classification.intent} />
                <MetaRow label="Risk" value={pipeline.classification.risk_level} />
                <MetaRow
                  label="Confidence"
                  value={`${Math.round(pipeline.classification.confidence * 100)}%`}
                />
              </div>
            ) : (
              <p className="text-sm text-[#65736f]">Awaiting first run.</p>
            )}
          </div>

          <ClarifyingQuestions
            questions={pipeline?.questions ?? []}
            answers={answers}
            needsClarification={pipeline?.needs_clarification ?? false}
            onAnswer={(id, answer) =>
              setAnswers((current) => ({ ...current, [id]: answer }))
            }
          />
        </section>

        <section className="min-w-0 space-y-4">
          <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
            <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-sm font-semibold">Prompt Variants</h2>
                <p className="text-xs text-[#65736f]">
                  {prompts.length ? `${prompts.length} scored variants` : "No variants yet"}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant={compareMode ? "default" : "outline"}
                  onClick={() => setCompareMode((value) => !value)}
                  disabled={!prompts.length}
                >
                  <GitCompare />
                  Compare
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={copySelectedPrompt}
                  disabled={!selectedPrompt}
                >
                  <Copy />
                  Copy
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={runSelectedPrompt}
                  disabled={!selectedPrompt || loading}
                >
                  <Play />
                  Run
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={saveSelectedPrompt}
                  disabled={!selectedPrompt || loading}
                >
                  <Save />
                  Save
                </Button>
              </div>
            </div>

            {compareMode && prompts.length ? (
              <PromptCompareGrid
                prompts={prompts}
                selectedId={selectedPrompt?.id}
                onSelect={setSelectedPromptId}
              />
            ) : (
              <div className="grid gap-3">
                {prompts.length ? (
                  prompts.map((prompt) => (
                    <PromptCard
                      key={prompt.id}
                      prompt={prompt}
                      selected={prompt.id === selectedPrompt?.id}
                      onSelect={() => setSelectedPromptId(prompt.id)}
                    />
                  ))
                ) : (
                  <div className="min-h-80 rounded-md border border-dashed border-[#c8d2ca] bg-[#fbfcf7] p-6 text-sm text-[#65736f]">
                    No prompt variants yet.
                  </div>
                )}
              </div>
            )}
          </div>

          <RunPromptPanel output={runOutput} selectedPrompt={selectedPrompt} />
        </section>

        <aside className="space-y-4">
          <PromptTuner settings={settings} onChange={setSettings} />
          <AgentTimeline timeline={timeline} status={status} />
        </aside>
      </div>
    </main>
  );
}

function DomainBadge({ label }: { label: string }) {
  return (
    <div className="inline-flex w-fit items-center gap-2 rounded-md border border-[#bfd0c2] bg-[#e9f2e9] px-2 py-1 text-xs font-medium text-[#214b40]">
      <Check className="size-3" />
      {label.replaceAll("_", " ")}
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[#eef1ec] py-1 last:border-0">
      <span className="text-[#65736f]">{label}</span>
      <span className="font-medium">{value.replaceAll("_", " ")}</span>
    </div>
  );
}

function ClarifyingQuestions({
  questions,
  answers,
  needsClarification,
  onAnswer,
}: {
  questions: { id: string; question: string; reason: string; required: boolean }[];
  answers: Record<string, string>;
  needsClarification: boolean;
  onAnswer: (id: string, answer: string) => void;
}) {
  return (
    <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold">Clarifying Questions</h2>
        {needsClarification ? (
          <span className="rounded-md bg-amber-100 px-2 py-1 text-xs text-amber-800">
            Open
          </span>
        ) : questions.length ? (
          <span className="rounded-md bg-emerald-100 px-2 py-1 text-xs text-emerald-800">
            Covered
          </span>
        ) : null}
      </div>
      <div className="space-y-3">
        {questions.length ? (
          questions.map((question) => (
            <label className="block" key={question.id}>
              <span className="mb-1 block text-sm font-medium">{question.question}</span>
              <input
                className="h-9 w-full rounded-md border border-[#ccd4ca] bg-[#fbfcf7] px-3 text-sm outline-none ring-[#4f7f74]/20 focus:ring-4"
                value={answers[question.id] ?? ""}
                onChange={(event) => onAnswer(question.id, event.target.value)}
              />
            </label>
          ))
        ) : (
          <p className="text-sm text-[#65736f]">Questions appear after generation.</p>
        )}
      </div>
    </div>
  );
}

function PromptTuner({
  settings,
  onChange,
}: {
  settings: PromptSettings;
  onChange: (settings: PromptSettings) => void;
}) {
  return (
    <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <SlidersHorizontal className="size-4 text-[#1e4d45]" />
        <h2 className="text-sm font-semibold">Tuner</h2>
      </div>
      <div className="space-y-4">
        {(Object.keys(settingOptions) as (keyof PromptSettings)[]).map((key) => (
          <div key={key}>
            <div className="mb-2 text-xs font-semibold uppercase text-[#65736f]">
              {key.replace("_", " ")}
            </div>
            <div className="grid grid-cols-2 gap-1 min-[380px]:grid-cols-3">
              {settingOptions[key].map((option) => (
                <button
                  key={option}
                  type="button"
                  className={cn(
                    "h-8 rounded-md border px-2 text-xs font-medium transition",
                    settings[key] === option
                      ? "border-[#1e4d45] bg-[#1e4d45] text-white"
                      : "border-[#d9ded2] bg-[#fbfcf7] text-[#34413e] hover:bg-[#edf1e8]",
                  )}
                  onClick={() => onChange({ ...settings, [key]: option })}
                >
                  {option.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function PromptCard({
  prompt,
  selected,
  onSelect,
}: {
  prompt: PromptVariant;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full rounded-md border bg-white p-4 text-left shadow-sm transition hover:border-[#78958e]",
        selected ? "border-[#1e4d45] ring-4 ring-[#b9d7ce]" : "border-[#d9ded2]",
      )}
    >
      <div className="mb-3 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold">{prompt.title}</h3>
            {prompt.recommendation_label === "recommended" ? (
              <span className="rounded-md bg-[#dbebe0] px-2 py-1 text-xs text-[#214b40]">
                Recommended
              </span>
            ) : null}
          </div>
          <p className="text-xs text-[#65736f]">{prompt.strategy.replaceAll("_", " ")}</p>
        </div>
        <div className="text-2xl font-semibold text-[#1e4d45]">
          {prompt.score_total ? Math.round(prompt.score_total * 100) : "--"}
        </div>
      </div>
      <ScoreBars scores={prompt.score_breakdown} />
      <p className="mt-3 line-clamp-4 whitespace-pre-wrap text-sm leading-6 text-[#34413e]">
        {prompt.prompt_text}
      </p>
    </button>
  );
}

function PromptCompareGrid({
  prompts,
  selectedId,
  onSelect,
}: {
  prompts: PromptVariant[];
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      {prompts.map((prompt) => (
        <button
          type="button"
          key={prompt.id}
          onClick={() => onSelect(prompt.id)}
          className={cn(
            "min-h-[420px] rounded-md border bg-[#fbfcf7] p-3 text-left shadow-sm",
            selectedId === prompt.id ? "border-[#1e4d45]" : "border-[#d9ded2]",
          )}
        >
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold">{prompt.title}</h3>
            <span className="text-lg font-semibold text-[#1e4d45]">
              {prompt.score_total ? Math.round(prompt.score_total * 100) : "--"}
            </span>
          </div>
          <ScoreBars scores={prompt.score_breakdown} compact />
          <p className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap text-xs leading-5 text-[#34413e]">
            {prompt.prompt_text}
          </p>
        </button>
      ))}
    </div>
  );
}

function ScoreBars({
  scores,
  compact = false,
}: {
  scores: Record<string, number>;
  compact?: boolean;
}) {
  const entries = Object.entries(scores);
  if (!entries.length) {
    return null;
  }
  return (
    <div className="grid gap-2">
      {entries.map(([key, value]) => (
        <div className="grid grid-cols-[minmax(110px,160px)_1fr_34px] items-center gap-2" key={key}>
          <span className={cn("truncate text-[#65736f]", compact ? "text-[11px]" : "text-xs")}>
            {key.replaceAll("_", " ")}
          </span>
          <span className="h-2 overflow-hidden rounded-full bg-[#dfe5dd]">
            <span
              className="block h-full rounded-full bg-[#1e4d45]"
              style={{ width: `${Math.round(value * 100)}%` }}
            />
          </span>
          <span className="text-right text-xs font-medium">{Math.round(value * 100)}</span>
        </div>
      ))}
    </div>
  );
}

function AgentTimeline({
  timeline,
  status,
}: {
  timeline: string[];
  status: string;
}) {
  const steps = ["classified", "questions_ready", "prompts_generated", "prompts_scored", "ready"];
  return (
    <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold">Timeline</h2>
        <span className="rounded-md bg-[#edf1e8] px-2 py-1 text-xs">{status}</span>
      </div>
      <div className="space-y-2">
        {steps.map((step) => {
          const done = timeline.includes(step);
          return (
            <div className="flex items-center gap-2" key={step}>
              <span
                className={cn(
                  "flex size-5 items-center justify-center rounded-full border",
                  done
                    ? "border-[#1e4d45] bg-[#1e4d45] text-white"
                    : "border-[#c8d2ca] bg-[#fbfcf7]",
                )}
              >
                {done ? <Check className="size-3" /> : null}
              </span>
              <span className="text-sm">{timelineLabels[step]}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function RunPromptPanel({
  output,
  selectedPrompt,
}: {
  output: string;
  selectedPrompt?: PromptVariant;
}) {
  return (
    <div className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold">Run Result</h2>
        <span className="max-w-52 truncate text-xs text-[#65736f]">
          {selectedPrompt?.title ?? "No prompt selected"}
        </span>
      </div>
      <pre className="min-h-28 whitespace-pre-wrap rounded-md bg-[#1d2523] p-3 text-xs leading-5 text-[#e8efe8]">
        {output || "Run output appears here."}
      </pre>
    </div>
  );
}
