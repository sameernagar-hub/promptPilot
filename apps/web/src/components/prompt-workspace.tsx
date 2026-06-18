"use client";

import {
  Check,
  Copy,
  FileText,
  GitCompare,
  History,
  ListChecks,
  Moon,
  Palette,
  Pencil,
  Play,
  RefreshCw,
  Save,
  Settings2,
  SkipForward,
  Sparkles,
  Sun,
  Zap,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import {
  confirmDomain,
  createSession,
  defaultSettings,
  getHealth,
  getProfile,
  getSession,
  ClarifyingQuestionState,
  PipelineResponse,
  RefinementMode,
  PromptSettings,
  PromptVariant,
  PromptRevision,
  runPipeline,
  runPrompt,
  savePrompt,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type WorkspaceProps = {
  initialSessionId?: string;
  initialCompare?: boolean;
};

type ThemeName = "sage" | "ink" | "paper";
type SettingKey = keyof PromptSettings;
type QuestionStates = Record<string, ClarifyingQuestionState>;

const sampleProblems = [
  "I need my bike fixed",
  "My React app saves successfully but the UI stays stale after clicking save.",
  "I need a better prompt for researching competitors in a new market.",
];

const settingOptions: {
  [Key in SettingKey]: readonly PromptSettings[Key][];
} = {
  target_platform: ["generic", "codex", "claude", "chatgpt", "gemini", "cursor"],
  detail_level: ["balanced", "concise", "exhaustive"],
  length: ["short", "medium", "deep"],
  skill_level: ["beginner", "practical", "expert"],
  tone: ["direct", "friendly", "technical"],
  formality: ["neutral", "casual", "formal"],
  temperature: ["balanced", "precise", "creative"],
  reasoning_style: ["ask_first", "direct_answer", "step_by_step", "explore_options"],
  source_strictness: ["none", "cite_when_needed", "official_only", "evidence_first"],
  interaction_mode: ["iterative", "one_shot", "agentic"],
  format: ["checklist", "guide", "table", "conversation", "plan"],
  risk: ["safe_only", "normal", "advanced"],
  sources: ["none", "web", "official_docs"],
} as const;

const settingGroups: { title: string; keys: SettingKey[] }[] = [
  {
    title: "Platform",
    keys: ["target_platform", "interaction_mode", "reasoning_style"],
  },
  {
    title: "Output",
    keys: ["detail_level", "formality", "temperature", "source_strictness", "format"],
  },
  {
    title: "Legacy Fit",
    keys: ["length", "skill_level", "tone", "risk", "sources"],
  },
];

const themeStyles: Record<
  ThemeName,
  {
    icon: ReactNode;
    page: string;
    header: string;
    card: string;
    subtle: string;
    border: string;
    primary: string;
    primaryText: string;
    soft: string;
    input: string;
  }
> = {
  sage: {
    icon: <Palette className="size-4" />,
    page: "bg-[#f6f7f2] text-[#1d2523]",
    header: "border-[#d9ded2] bg-[#fbfcf7]",
    card: "border-[#d9ded2] bg-white",
    subtle: "text-[#65736f]",
    border: "border-[#d9ded2]",
    primary: "bg-[#1e4d45]",
    primaryText: "text-[#1e4d45]",
    soft: "bg-[#edf1e8]",
    input: "border-[#ccd4ca] bg-[#fbfcf7] focus:ring-[#4f7f74]/20",
  },
  ink: {
    icon: <Moon className="size-4" />,
    page: "bg-[#101417] text-[#f3f5ee]",
    header: "border-[#2b3338] bg-[#151b1f]",
    card: "border-[#2b3338] bg-[#171e22]",
    subtle: "text-[#9ba7a5]",
    border: "border-[#2b3338]",
    primary: "bg-[#d6f36b]",
    primaryText: "text-[#d6f36b]",
    soft: "bg-[#232b2f]",
    input: "border-[#344047] bg-[#101417] focus:ring-[#d6f36b]/20",
  },
  paper: {
    icon: <Sun className="size-4" />,
    page: "bg-[#fafafa] text-[#202124]",
    header: "border-[#dddddd] bg-white",
    card: "border-[#dddddd] bg-white",
    subtle: "text-[#646970]",
    border: "border-[#dddddd]",
    primary: "bg-[#2f5f9f]",
    primaryText: "text-[#2f5f9f]",
    soft: "bg-[#eef3f8]",
    input: "border-[#cfd6dd] bg-white focus:ring-[#2f5f9f]/20",
  },
};

export function PromptWorkspace({
  initialSessionId,
  initialCompare = false,
}: WorkspaceProps) {
  const [theme, setTheme] = useState<ThemeName>("sage");
  const styles = themeStyles[theme];
  const [problem, setProblem] = useState("");
  const [settings, setSettings] = useState<PromptSettings>(defaultSettings);
  const [refinementMode, setRefinementMode] = useState<RefinementMode>("refinement");
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId ?? null);
  const [sessionProblem, setSessionProblem] = useState("");
  const [pipeline, setPipeline] = useState<PipelineResponse | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [questionStates, setQuestionStates] = useState<QuestionStates>({});
  const [selectedPromptId, setSelectedPromptId] = useState<string | null>(null);
  const [customDomain, setCustomDomain] = useState("");
  const [runOutput, setRunOutput] = useState("");
  const [status, setStatus] = useState("Idle");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(initialCompare);
  const [apiHealth, setApiHealth] = useState<"ok" | "degraded" | "offline">("offline");

  useEffect(() => {
    getHealth()
      .then((health) => setApiHealth(health.status === "ok" ? "ok" : "degraded"))
      .catch(() => setApiHealth("offline"));
  }, []);

  useEffect(() => {
    if (initialSessionId) {
      return;
    }
    getProfile()
      .then((profile) => {
        const preference = profile.platform_preferences[0]?.preference;
        if (preference) {
          setSettings((current) => mergePromptSettings(current, preference));
        }
      })
      .catch(() => {
        // Profile defaults are a convenience; the workspace can run without them.
      });
  }, [initialSessionId]);

  useEffect(() => {
    if (!initialSessionId) {
      return;
    }
    getSession(initialSessionId)
      .then((session) => {
        setProblem(session.raw_input);
        setSessionProblem(session.raw_input);
        setSettings({ ...defaultSettings, ...session.user_settings });
        const loadedAnswers: Record<string, string> = { ...(session.answers ?? {}) };
        const loadedStates: QuestionStates = {};
        for (const question of session.clarifying_questions ?? []) {
          loadedStates[question.id] = question.state ?? "unanswered";
          if (question.answer) {
            loadedAnswers[question.id] = question.answer;
          }
        }
        setAnswers(loadedAnswers);
        setQuestionStates(loadedStates);
        setStatus(session.status);
      })
      .catch((caught: unknown) =>
        setError(caught instanceof Error ? caught.message : "Session not found"),
      );
  }, [initialSessionId]);

  const prompts = useMemo(() => pipeline?.prompts ?? [], [pipeline?.prompts]);
  const recommendedPrompt = useMemo(
    () =>
      prompts.find((prompt) => prompt.id === pipeline?.recommended_prompt_id) ??
      prompts.find((prompt) => prompt.recommendation_label === "recommended") ??
      prompts[0],
    [pipeline?.recommended_prompt_id, prompts],
  );
  const selectedPrompt = useMemo(
    () =>
      prompts.find((prompt) => prompt.id === selectedPromptId) ??
      recommendedPrompt,
    [prompts, recommendedPrompt, selectedPromptId],
  );

  function applyPipelineResult(result: PipelineResponse) {
    setPipeline(result);
    setSelectedPromptId(result.recommended_prompt_id);
    setCustomDomain(result.classification.domain.replaceAll("_", " "));
    setAnswers((current) => {
      const merged = { ...current };
      for (const question of result.questions) {
        if (question.answer) {
          merged[question.id] = question.answer;
        } else if (question.state === "skipped") {
          merged[question.id] = "";
        }
      }
      return merged;
    });
    setQuestionStates((current) => {
      const merged = { ...current };
      for (const question of result.questions) {
        merged[question.id] = question.state ?? "unanswered";
      }
      return merged;
    });
    if (result.classification.needs_domain_confirmation) {
      setStatus("Confirm domain");
    } else if (result.needs_clarification && !result.prompts.length) {
      setStatus("Answer questions");
    } else if (result.assumptions.length) {
      setStatus("Ready with assumptions");
    } else {
      setStatus("Ready");
    }
  }

  async function generate(
    nextAnswers = answers,
    nextQuestionStates = questionStates,
    nextMode = refinementMode,
  ) {
    if (!problem.trim()) {
      setError("Enter a problem first.");
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
      const submittedAnswers = shouldCreateSession ? {} : nextAnswers;
      const submittedStates = shouldCreateSession ? {} : nextQuestionStates;
      if (shouldCreateSession) {
        setSessionId(session.id);
        setSessionProblem(problem.trim());
        setAnswers({});
        setQuestionStates({});
      }
      const result = await runPipeline(
        session.id,
        settings,
        submittedAnswers,
        submittedStates,
        nextMode,
      );
      applyPipelineResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Generation failed");
      setStatus("Error");
    } finally {
      setLoading(false);
    }
  }

  async function handleDomainConfirm(accepted: boolean) {
    if (!sessionId || !pipeline) {
      return;
    }
    const domain = accepted ? pipeline.classification.domain : customDomain.trim();
    if (!domain) {
      setError("Enter the correct domain.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const confirmed = await confirmDomain(sessionId, domain, accepted);
      setPipeline({ ...pipeline, classification: confirmed.classification });
      const result = await runPipeline(
        sessionId,
        settings,
        answers,
        questionStates,
        refinementMode,
      );
      applyPipelineResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Domain update failed");
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

  function resetWithSample() {
    setProblem(sampleProblems[Math.floor(Math.random() * sampleProblems.length)]);
    setSessionId(null);
    setSessionProblem("");
    setPipeline(null);
    setAnswers({});
    setQuestionStates({});
    setSelectedPromptId(null);
    setRunOutput("");
    setStatus("Idle");
  }

  const healthClass =
    apiHealth === "ok"
      ? "bg-emerald-500"
      : apiHealth === "degraded"
        ? "bg-amber-500"
        : "bg-rose-500";

  return (
    <main className={cn("min-h-screen", styles.page)}>
      <header className={cn("border-b", styles.header)}>
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("flex size-9 items-center justify-center rounded-md text-white", styles.primary)}>
              <Sparkles className="size-4" />
            </div>
            <div>
              <h1 className="text-lg font-semibold leading-tight">PromptPilot</h1>
              <p className={cn("text-xs", styles.subtle)}>{status}</p>
            </div>
          </div>
          <nav className="flex flex-wrap items-center gap-2 text-sm">
            <Link className={navClass(styles)} href="/">Workspace</Link>
            <Link className={navClass(styles)} href="/profile">Profile</Link>
            <Link className={navClass(styles)} href="/profile/imports">Imports</Link>
            <Link className={navClass(styles)} href="/library">Library</Link>
            <Link className={navClass(styles)} href="/settings">Settings</Link>
            <span className={cn("inline-flex items-center gap-2 rounded-md border px-2 py-1 text-xs", styles.border, styles.soft)}>
              <span className={cn("size-2 rounded-full", healthClass)} />
              API {apiHealth}
            </span>
          </nav>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-4 px-4 py-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <section className="space-y-4">
          <div className={cardClass(styles)}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <h2 className="text-sm font-semibold">Request</h2>
              <Button type="button" size="sm" variant="outline" onClick={resetWithSample}>
                <RefreshCw />
                Sample
              </Button>
            </div>
            <textarea
              className={cn("min-h-44 w-full resize-y rounded-md border p-3 text-sm leading-6 outline-none focus:ring-4", styles.input)}
              value={problem}
              onChange={(event) => setProblem(event.target.value)}
              placeholder="I need my bike fixed"
            />
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button type="button" onClick={() => generate()} disabled={loading}>
                <Sparkles />
                {loading
                  ? "Thinking"
                  : refinementMode === "refinement"
                    ? "Start refinement"
                    : "Generate prompt"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowSettings((value) => !value)}
              >
                <Settings2 />
                Preferences
              </Button>
              <ModeToggle
                mode={refinementMode}
                onChange={setRefinementMode}
                styles={styles}
              />
              <ThemePicker theme={theme} onChange={setTheme} />
            </div>
            {error ? (
              <p className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
                {error}
              </p>
            ) : null}
          </div>

          {showSettings ? (
            <PreferencesPanel settings={settings} onChange={setSettings} styles={styles} />
          ) : null}

          {pipeline ? (
            <DomainPanel
              classification={pipeline.classification}
              customDomain={customDomain}
              setCustomDomain={setCustomDomain}
              onConfirm={() => handleDomainConfirm(true)}
              onCorrect={() => handleDomainConfirm(false)}
              loading={loading}
              styles={styles}
            />
          ) : null}

          <QuestionsPanel
            questions={pipeline?.questions ?? []}
            answers={answers}
            questionStates={questionStates}
            needsClarification={pipeline?.needs_clarification ?? false}
            assumptions={pipeline?.assumptions ?? []}
            onAnswer={(id, answer) => {
              setAnswers((current) => ({ ...current, [id]: answer }));
              setQuestionStates((current) => ({
                ...current,
                [id]: answer.trim().length ? "answered" : "unanswered",
              }));
            }}
            onSkip={(id) => {
              setAnswers((current) => ({ ...current, [id]: "" }));
              setQuestionStates((current) => ({ ...current, [id]: "skipped" }));
            }}
            onRevise={(id) =>
              setQuestionStates((current) => ({ ...current, [id]: "unanswered" }))
            }
            onUpdate={() => generate()}
            loading={loading}
            styles={styles}
          />
        </section>

        <section className="space-y-4">
          <RecommendedPrompt
            prompt={selectedPrompt}
            recommendedPromptId={recommendedPrompt?.id ?? null}
            styles={styles}
            onCopy={copySelectedPrompt}
            onRun={runSelectedPrompt}
            onSave={saveSelectedPrompt}
            loading={loading}
          />

          {pipeline?.revisions.length ? (
            <RevisionHistory revisions={pipeline.revisions} styles={styles} />
          ) : null}

          {runOutput ? (
            <div className={cardClass(styles)}>
              <div className="mb-3 flex items-center gap-2">
                <Play className={cn("size-4", styles.primaryText)} />
                <h2 className="text-sm font-semibold">Run Result</h2>
              </div>
              <pre className="whitespace-pre-wrap rounded-md bg-[#101417] p-3 text-xs leading-5 text-[#f3f5ee]">
                {runOutput}
              </pre>
            </div>
          ) : null}

          <div className={cardClass(styles)}>
            <button
              type="button"
              className="flex w-full items-center justify-between gap-3 text-left"
              onClick={() => setShowAlternatives((value) => !value)}
            >
              <span className="flex items-center gap-2 text-sm font-semibold">
                <GitCompare className={cn("size-4", styles.primaryText)} />
                Alternatives
              </span>
              <span className={cn("text-xs", styles.subtle)}>
                {prompts.length ? `${Math.max(prompts.length - 1, 0)} more` : "None"}
              </span>
            </button>
            {showAlternatives ? (
              <div className="mt-3 grid gap-3">
                {prompts
                  .filter((prompt) => prompt.id !== recommendedPrompt?.id)
                  .map((prompt) => (
                    <AlternativePrompt
                      key={prompt.id}
                      prompt={prompt}
                      selected={prompt.id === selectedPrompt?.id}
                      onSelect={() => setSelectedPromptId(prompt.id)}
                      styles={styles}
                    />
                  ))}
                {!prompts.length ? (
                  <p className={cn("text-sm", styles.subtle)}>Generate once to see alternatives.</p>
                ) : null}
              </div>
            ) : null}
          </div>
        </section>
      </div>
    </main>
  );
}

function DomainPanel({
  classification,
  customDomain,
  setCustomDomain,
  onConfirm,
  onCorrect,
  loading,
  styles,
}: {
  classification: PipelineResponse["classification"];
  customDomain: string;
  setCustomDomain: (value: string) => void;
  onConfirm: () => void;
  onCorrect: () => void;
  loading: boolean;
  styles: (typeof themeStyles)[ThemeName];
}) {
  const needsConfirmation =
    classification.needs_domain_confirmation && classification.domain_source === "detected";
  return (
    <div className={cardClass(styles)}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold">Domain</h2>
          <p className={cn("text-xs", styles.subtle)}>
            {classification.subdomain ?? "Open request"} / {Math.round(classification.confidence * 100)}%
          </p>
        </div>
        <span className={cn("rounded-md px-2 py-1 text-xs", needsConfirmation ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800")}>
          {needsConfirmation ? "Confirm" : "Set"}
        </span>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        <span className={cn("rounded-md px-2 py-1 text-sm font-medium", styles.soft)}>
          {labelize(classification.domain)}
        </span>
        {classification.alternative_domains.slice(0, 3).map((domain) => (
          <button
            key={domain}
            type="button"
            className={cn("rounded-md border px-2 py-1 text-sm", styles.border)}
            onClick={() => setCustomDomain(labelize(domain))}
          >
            {labelize(domain)}
          </button>
        ))}
      </div>
      {needsConfirmation ? (
        <div className="space-y-2">
          <input
            className={cn("h-9 w-full rounded-md border px-3 text-sm outline-none focus:ring-4", styles.input)}
            value={customDomain}
            onChange={(event) => setCustomDomain(event.target.value)}
          />
          <div className="flex flex-wrap gap-2">
            <Button type="button" size="sm" onClick={onConfirm} disabled={loading}>
              <Check />
              Yes
            </Button>
            <Button type="button" size="sm" variant="outline" onClick={onCorrect} disabled={loading}>
              Use typed domain
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function QuestionsPanel({
  questions,
  answers,
  questionStates,
  needsClarification,
  assumptions,
  onAnswer,
  onSkip,
  onRevise,
  onUpdate,
  loading,
  styles,
}: {
  questions: {
    id: string;
    question: string;
    reason: string;
    required: boolean;
    answer?: string | null;
    state?: ClarifyingQuestionState;
    revision_count?: number;
  }[];
  answers: Record<string, string>;
  questionStates: QuestionStates;
  needsClarification: boolean;
  assumptions: string[];
  onAnswer: (id: string, answer: string) => void;
  onSkip: (id: string) => void;
  onRevise: (id: string) => void;
  onUpdate: () => void;
  loading: boolean;
  styles: (typeof themeStyles)[ThemeName];
}) {
  return (
    <div className={cardClass(styles)}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-semibold">Questions</h2>
        {questions.length ? (
          <span className={cn("rounded-md px-2 py-1 text-xs", needsClarification ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800")}>
            {needsClarification ? "Open" : "Covered"}
          </span>
        ) : null}
      </div>
      <div className="space-y-3">
        {questions.length ? (
          questions.map((question) => {
            const state =
              questionStates[question.id] ?? question.state ?? "unanswered";
            const isSkipped = state === "skipped";
            const isAnswered = state === "answered";
            return (
              <div className={cn("rounded-md border p-3", styles.border)} key={question.id}>
                <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
                  <label className="block min-w-0 flex-1">
                    <span className="block text-sm font-medium">{question.question}</span>
                    <span className={cn("mt-1 block text-xs leading-5", styles.subtle)}>
                      {question.reason}
                    </span>
                  </label>
                  <span className={questionStateClass(state)}>
                    {isSkipped
                      ? "Skipped"
                      : isAnswered
                        ? question.revision_count
                          ? "Revised"
                          : "Answered"
                        : question.required
                          ? "Required"
                          : "Optional"}
                  </span>
                </div>
                <textarea
                  className={cn("min-h-20 w-full resize-y rounded-md border p-3 text-sm leading-5 outline-none focus:ring-4", styles.input)}
                  value={answers[question.id] ?? ""}
                  onChange={(event) => onAnswer(question.id, event.target.value)}
                  disabled={isSkipped}
                />
                <div className="mt-2 flex flex-wrap gap-2">
                  {isSkipped ? (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => onRevise(question.id)}
                    >
                      <Pencil />
                      Revise
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => onSkip(question.id)}
                    >
                      <SkipForward />
                      Skip
                    </Button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <p className={cn("text-sm", styles.subtle)}>Questions appear after generation.</p>
        )}
      </div>
      {assumptions.length ? (
        <div className={cn("mt-3 rounded-md border p-3 text-xs leading-5", styles.border, styles.soft)}>
          <div className="mb-1 font-medium">Assumptions</div>
          {assumptions.map((assumption) => (
            <div key={assumption}>- {assumption}</div>
          ))}
        </div>
      ) : null}
      {questions.length ? (
        <Button className="mt-3" type="button" variant="outline" onClick={onUpdate} disabled={loading}>
          <RefreshCw />
          {needsClarification ? "Continue" : "Update prompt"}
        </Button>
      ) : null}
    </div>
  );
}

function RecommendedPrompt({
  prompt,
  recommendedPromptId,
  styles,
  onCopy,
  onRun,
  onSave,
  loading,
}: {
  prompt?: PromptVariant;
  recommendedPromptId: string | null;
  styles: (typeof themeStyles)[ThemeName];
  onCopy: () => void;
  onRun: () => void;
  onSave: () => void;
  loading: boolean;
}) {
  return (
    <div className={cardClass(styles)}>
      <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-sm font-semibold">
            {prompt?.id === recommendedPromptId ? "Recommended Prompt" : "Selected Prompt"}
          </h2>
          <p className={cn("text-xs", styles.subtle)}>
            {prompt?.score_total ? `${Math.round(prompt.score_total * 100)} score` : "Ready after generation"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={onCopy} disabled={!prompt}>
            <Copy />
            Copy
          </Button>
          <Button type="button" variant="outline" onClick={onRun} disabled={!prompt || loading}>
            <Play />
            Run
          </Button>
          <Button type="button" variant="outline" onClick={onSave} disabled={!prompt || loading}>
            <Save />
            Save
          </Button>
        </div>
      </div>
      {prompt ? (
        <div className={cn("rounded-md border p-4", styles.border, styles.soft)}>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <FileText className={cn("size-4", styles.primaryText)} />
            <span className="font-medium">{prompt.title}</span>
            {prompt.id === recommendedPromptId ? (
              <span className="rounded-md bg-emerald-100 px-2 py-1 text-xs text-emerald-800">
                Recommended
              </span>
            ) : null}
          </div>
          {prompt.explanation ? (
            <p className={cn("mb-3 rounded-md bg-white/60 px-3 py-2 text-xs leading-5", styles.subtle)}>
              {prompt.explanation}
            </p>
          ) : null}
          <pre className="whitespace-pre-wrap break-words text-sm leading-7">
            {prompt.prompt_text}
          </pre>
        </div>
      ) : (
        <div className={cn("min-h-80 rounded-md border border-dashed p-6 text-sm", styles.border, styles.subtle)}>
          No prompt generated yet.
        </div>
      )}
    </div>
  );
}

function AlternativePrompt({
  prompt,
  selected,
  onSelect,
  styles,
}: {
  prompt: PromptVariant;
  selected: boolean;
  onSelect: () => void;
  styles: (typeof themeStyles)[ThemeName];
}) {
  return (
    <button
      type="button"
      className={cn("rounded-md border p-3 text-left", styles.border, selected ? styles.soft : "")}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">{prompt.title}</h3>
          <p className={cn("text-xs", styles.subtle)}>{labelize(prompt.strategy)}</p>
        </div>
        <span className={cn("text-sm font-semibold", styles.primaryText)}>
          {prompt.score_total ? Math.round(prompt.score_total * 100) : "--"}
        </span>
      </div>
      <p className={cn("mt-2 line-clamp-3 text-xs leading-5", styles.subtle)}>
        {prompt.prompt_text}
      </p>
    </button>
  );
}

function PreferencesPanel({
  settings,
  onChange,
  styles,
}: {
  settings: PromptSettings;
  onChange: (settings: PromptSettings) => void;
  styles: (typeof themeStyles)[ThemeName];
}) {
  return (
    <div className={cardClass(styles)}>
      <div className="mb-3 flex items-center gap-2">
        <Settings2 className={cn("size-4", styles.primaryText)} />
        <h2 className="text-sm font-semibold">Preferences</h2>
      </div>
      <div className="space-y-4">
        {settingGroups.map((group) => (
          <div className={cn("rounded-md border p-3", styles.border)} key={group.title}>
            <div className="mb-2 text-xs font-semibold uppercase tracking-normal">
              {group.title}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {group.keys.map((key) => (
                <label className="space-y-1 text-xs font-medium" key={key}>
                  <span>{labelize(key)}</span>
                  <select
                    className={cn("h-9 w-full rounded-md border px-2 text-sm outline-none focus:ring-4", styles.input)}
                    value={settings[key]}
                    onChange={(event) =>
                      onChange({
                        ...settings,
                        [key]: event.target.value as PromptSettings[typeof key],
                      })
                    }
                  >
                    {settingOptions[key].map((option) => (
                      <option key={option} value={option}>
                        {optionLabel(option)}
                      </option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ModeToggle({
  mode,
  onChange,
  styles,
}: {
  mode: RefinementMode;
  onChange: (mode: RefinementMode) => void;
  styles: (typeof themeStyles)[ThemeName];
}) {
  return (
    <div className={cn("flex rounded-md border p-1", styles.border, styles.soft)}>
      <button
        type="button"
        className={modeButtonClass(mode === "refinement", styles)}
        onClick={() => onChange("refinement")}
        title="Refinement mode"
      >
        <ListChecks className="size-4" />
        Refine
      </button>
      <button
        type="button"
        className={modeButtonClass(mode === "quick", styles)}
        onClick={() => onChange("quick")}
        title="Quick generation mode"
      >
        <Zap className="size-4" />
        Quick
      </button>
    </div>
  );
}

function RevisionHistory({
  revisions,
  styles,
}: {
  revisions: PromptRevision[];
  styles: (typeof themeStyles)[ThemeName];
}) {
  return (
    <div className={cardClass(styles)}>
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="flex items-center gap-2 text-sm font-semibold">
          <History className={cn("size-4", styles.primaryText)} />
          Revisions
        </span>
        <span className={cn("text-xs", styles.subtle)}>{revisions.length} stored</span>
      </div>
      <div className="space-y-2">
        {revisions.slice(0, 4).map((revision) => (
          <div className={cn("rounded-md border p-3", styles.border)} key={revision.id}>
            <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs font-medium">{labelize(revision.revision_type)}</span>
              <span className={cn("text-xs", styles.subtle)}>
                {new Date(revision.created_at).toLocaleString()}
              </span>
            </div>
            {revision.rationale ? (
              <p className={cn("text-xs leading-5", styles.subtle)}>{revision.rationale}</p>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}

function ThemePicker({
  theme,
  onChange,
}: {
  theme: ThemeName;
  onChange: (theme: ThemeName) => void;
}) {
  return (
    <div className="flex rounded-md border border-black/10 bg-white/70 p-1">
      {(Object.keys(themeStyles) as ThemeName[]).map((name) => (
        <button
          key={name}
          type="button"
          className={cn(
            "flex size-8 items-center justify-center rounded-md text-[#1d2523]",
            theme === name ? "bg-[#1e4d45] text-white" : "hover:bg-black/5",
          )}
          onClick={() => onChange(name)}
          title={name}
        >
          {themeStyles[name].icon}
        </button>
      ))}
    </div>
  );
}

function cardClass(styles: (typeof themeStyles)[ThemeName]) {
  return cn("rounded-md border p-4 shadow-sm", styles.card);
}

function navClass(styles: (typeof themeStyles)[ThemeName]) {
  return cn("rounded-md px-2 py-1 hover:opacity-80", styles.soft);
}

function modeButtonClass(active: boolean, styles: (typeof themeStyles)[ThemeName]) {
  return cn(
    "flex h-8 items-center gap-1 rounded-md px-2 text-xs font-medium",
    active ? cn(styles.primary, "text-white") : "hover:bg-white/60",
  );
}

function questionStateClass(state: ClarifyingQuestionState) {
  return cn(
    "rounded-md px-2 py-1 text-xs font-medium",
    state === "answered"
      ? "bg-emerald-100 text-emerald-800"
      : state === "skipped"
        ? "bg-amber-100 text-amber-800"
        : "bg-slate-100 text-slate-700",
  );
}

function mergePromptSettings(
  current: PromptSettings,
  preference: Partial<PromptSettings>,
) {
  const merged = { ...current };
  for (const key of Object.keys(settingOptions) as SettingKey[]) {
    const value = preference[key];
    if (value && (settingOptions[key] as readonly string[]).includes(value)) {
      Object.assign(merged, { [key]: value });
    }
  }
  return merged;
}

function optionLabel(value: string) {
  const labels: Record<string, string> = {
    chatgpt: "ChatGPT",
    codex: "Codex",
    claude: "Claude",
    gemini: "Gemini",
    cursor: "Cursor",
  };
  return labels[value] ?? labelize(value);
}

function labelize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
