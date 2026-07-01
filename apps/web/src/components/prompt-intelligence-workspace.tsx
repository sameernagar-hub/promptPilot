"use client";

import {
  Brain,
  Database,
  FileText,
  Gauge,
  Lightbulb,
  RefreshCw,
  SearchCheck,
  ShieldCheck,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import {
  analyzePromptIntelligence,
  ConversationImport,
  getImports,
  getLatestPromptIntelligenceReport,
  getPromptIntelligenceReports,
  ImportPlatform,
  ImportSourceType,
  PromptIntelligenceReport,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const platformOptions: { value: ImportPlatform; label: string }[] = [
  { value: "codex", label: "Codex" },
  { value: "claude", label: "Claude" },
  { value: "chatgpt", label: "ChatGPT" },
  { value: "cursor", label: "Cursor" },
  { value: "gemini", label: "Gemini" },
  { value: "windsurf", label: "Windsurf" },
  { value: "manual", label: "Manual" },
  { value: "generic", label: "Generic" },
];

const sourceOptions: { value: ImportSourceType; label: string }[] = [
  { value: "markdown", label: "Markdown" },
  { value: "paste", label: "Paste" },
  { value: "json", label: "JSON" },
  { value: "text", label: "Text" },
  { value: "manual", label: "Manual" },
];

export function PromptIntelligenceWorkspace() {
  const [imports, setImports] = useState<ConversationImport[]>([]);
  const [reports, setReports] = useState<PromptIntelligenceReport[]>([]);
  const [report, setReport] = useState<PromptIntelligenceReport | null>(null);
  const [platform, setPlatform] = useState<ImportPlatform>("codex");
  const [sourceType, setSourceType] = useState<ImportSourceType>("markdown");
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [status, setStatus] = useState("Loading");
  const [error, setError] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    void refresh();
  }, []);

  const totalMessages = useMemo(
    () => imports.reduce((sum, item) => sum + item.message_count, 0),
    [imports],
  );

  async function refresh() {
    setRefreshing(true);
    setError("");
    try {
      const [importRows, reportRows, latest] = await Promise.all([
        getImports(),
        getPromptIntelligenceReports(),
        getLatestPromptIntelligenceReport(),
      ]);
      setImports(importRows);
      setReports(reportRows);
      setReport(latest ?? reportRows[0] ?? null);
      setStatus(latest ? "Profile judged" : importRows.length ? "Ready to judge" : "Ready");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Prompt intelligence unavailable");
      setStatus("Offline");
    } finally {
      setRefreshing(false);
    }
  }

  async function submitForJudgment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!rawText.trim()) {
      setError("Paste or upload a prompt session first");
      return;
    }
    setAnalyzing(true);
    setError("");
    try {
      const nextReport = await analyzePromptIntelligence({
        platform,
        source_type: sourceType,
        title: title.trim() || null,
        raw_text: rawText,
      });
      setReport(nextReport);
      setReports((current) => [
        nextReport,
        ...current.filter((item) => item.id !== nextReport.id),
      ]);
      if (nextReport.source_import) {
        setImports((current) => [
          nextReport.source_import as ConversationImport,
          ...current.filter((item) => item.id !== nextReport.source_import?.id),
        ]);
      }
      setRawText("");
      setTitle("");
      setStatus("Judged");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Judgment failed");
    } finally {
      setAnalyzing(false);
    }
  }

  async function judgeExistingImport(item: ConversationImport) {
    setAnalyzing(true);
    setError("");
    try {
      const nextReport = await analyzePromptIntelligence({ import_id: item.id });
      setReport(nextReport);
      setReports((current) => [
        nextReport,
        ...current.filter((existing) => existing.id !== nextReport.id),
      ]);
      setStatus("Judged import");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Judgment failed");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleFileUpload(file: File | null) {
    if (!file) {
      return;
    }
    setError("");
    try {
      const text = await file.text();
      setRawText(text);
      if (!title.trim()) {
        setTitle(file.name.replace(/\.[^.]+$/, ""));
      }
      const extension = file.name.split(".").pop()?.toLowerCase();
      if (extension === "json") {
        setSourceType("json");
      } else if (extension === "md" || extension === "markdown") {
        setSourceType("markdown");
      } else {
        setSourceType("text");
      }
      setStatus("Loaded");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "File upload failed");
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  return (
    <AppShell
      title="Prompt Intelligence Profile"
      status={status}
      icon={<Brain className="size-4" />}
      actions={
        <Button type="button" variant="outline" onClick={refresh} disabled={refreshing}>
          <RefreshCw className={cn(refreshing ? "animate-spin" : "")} />
          Refresh
        </Button>
      }
    >
      <div className="mx-auto max-w-6xl px-4 py-4">
        {error ? (
          <p className="mb-4 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
            {error}
          </p>
        ) : null}

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric icon={<Database className="size-4" />} label="Imports" value={imports.length} />
          <Metric icon={<FileText className="size-4" />} label="Messages" value={totalMessages} />
          <Metric icon={<Gauge className="size-4" />} label="Reports" value={reports.length} />
          <Metric
            icon={<ShieldCheck className="size-4" />}
            label="Provider"
            value={report?.provider === "openai" ? "OpenAI" : "Local"}
          />
        </section>

        <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
          <section className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <UploadCloud className="size-4 text-[#1e4d45]" />
                <h2 className="text-sm font-semibold">Import Prompt Session</h2>
              </div>
              <span className="rounded-md bg-[#e9f2f6] px-2 py-1 text-xs text-[#295061]">
                {rawText.length.toLocaleString()} chars
              </span>
            </div>
            <form className="space-y-3" onSubmit={submitForJudgment}>
              <div className="grid gap-3 sm:grid-cols-2">
                <SelectField
                  label="Platform"
                  value={platform}
                  onChange={(value) => setPlatform(value as ImportPlatform)}
                  options={platformOptions}
                />
                <SelectField
                  label="Source"
                  value={sourceType}
                  onChange={(value) => setSourceType(value as ImportSourceType)}
                  options={sourceOptions}
                />
              </div>
              <label className="block space-y-1 text-xs font-medium text-[#34413e]">
                <span>Title</span>
                <input
                  className="h-9 w-full rounded-md border border-[#cbd5cd] bg-white px-2 text-sm outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="Phase 16 Codex session"
                />
              </label>
              <label className="block space-y-1 text-xs font-medium text-[#34413e]">
                <span>Prompt Session</span>
                <textarea
                  className="min-h-72 w-full resize-y rounded-md border border-[#cbd5cd] bg-white p-3 text-sm leading-6 outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
                  value={rawText}
                  onChange={(event) => setRawText(event.target.value)}
                  placeholder="User: I need Codex to..."
                />
              </label>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <input
                  ref={fileInputRef}
                  className="hidden"
                  type="file"
                  accept=".txt,.md,.markdown,.json,text/plain,application/json,text/markdown"
                  onChange={(event) => handleFileUpload(event.target.files?.[0] ?? null)}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <UploadCloud />
                  Upload
                </Button>
                <Button type="submit" disabled={analyzing}>
                  <SearchCheck />
                  {analyzing ? "Judging" : "Judge My Prompts"}
                </Button>
              </div>
            </form>
          </section>

          <CurrentReport report={report} analyzing={analyzing} />
        </div>

        {report ? (
          <div className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
            <section>
              <div className="mb-2 flex items-center gap-2">
                <Gauge className="size-4 text-[#1e4d45]" />
                <h2 className="text-sm font-semibold">Style Scores</h2>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {report.style_scores.map((score) => (
                  <ScoreCard key={score.key} score={score} />
                ))}
              </div>
            </section>

            <section className="space-y-4">
              <Panel title="Behavior Patterns" icon={<Brain className="size-4" />}>
                {report.behavior_patterns.map((pattern) => (
                  <PatternItem key={pattern.title} pattern={pattern} />
                ))}
              </Panel>
              <Panel title="Next Prompt Recipe" icon={<Sparkles className="size-4" />}>
                <ol className="space-y-2">
                  {report.next_prompt_recipe.map((item, index) => (
                    <li key={`${item}-${index}`} className="flex gap-2 text-sm leading-6">
                      <span className="flex size-6 shrink-0 items-center justify-center rounded-md bg-[#e9f2f6] text-xs font-semibold text-[#295061]">
                        {index + 1}
                      </span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ol>
              </Panel>
            </section>
          </div>
        ) : null}

        {report ? (
          <section className="mt-4 grid gap-4 lg:grid-cols-2">
            <Panel title="Recommendations" icon={<Lightbulb className="size-4" />}>
              {report.recommendations.map((item) => (
                <RecommendationItem key={item.title} item={item} />
              ))}
            </Panel>
            <Panel title="Comparisons" icon={<SearchCheck className="size-4" />}>
              {report.comparisons.map((item) => (
                <div key={item.label} className="border-b border-[#eef1ec] py-3 last:border-0">
                  <div className="text-sm font-semibold">{item.label}</div>
                  <p className="mt-1 text-sm leading-6 text-[#34413e]">{item.detail}</p>
                </div>
              ))}
            </Panel>
          </section>
        ) : null}

        <section className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_24rem]">
          <ImportLedger
            imports={imports}
            analyzing={analyzing}
            onJudge={judgeExistingImport}
          />
          <ReportHistory
            reports={reports}
            selectedId={report?.id ?? null}
            onSelect={setReport}
          />
        </section>
      </div>
    </AppShell>
  );
}

function CurrentReport({
  report,
  analyzing,
}: {
  report: PromptIntelligenceReport | null;
  analyzing: boolean;
}) {
  if (!report) {
    return (
      <section className="rounded-md border border-dashed border-[#c8d2ca] bg-white p-6 shadow-sm">
        <div className="mb-3 flex items-center gap-2 text-[#1d2523]">
          <SearchCheck className="size-4" />
          <h2 className="text-sm font-semibold">Ready To Judge</h2>
        </div>
        <p className="text-sm leading-6 text-[#65736f]">
          Paste or upload a prompt session, then let PromptPilot read your prompting
          behavior like a profile instead of a template.
        </p>
        <div className="mt-4 grid gap-2 text-sm text-[#34413e] sm:grid-cols-2">
          <MiniSignal label="Scores" value="style" />
          <MiniSignal label="Evidence" value="excerpts" />
          <MiniSignal label="Advice" value="upgrades" />
          <MiniSignal label="Mode" value={analyzing ? "thinking" : "idle"} />
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-2 text-[#1e4d45]">
            <Brain className="size-4" />
            <span className="text-xs font-medium uppercase tracking-wide">Current Judgment</span>
          </div>
          <h2 className="text-xl font-semibold leading-7">{report.headline}</h2>
        </div>
        <span className="rounded-md bg-[#dbebe0] px-2 py-1 text-xs font-medium text-[#214b40]">
          {report.provider} / {report.model}
        </span>
      </div>
      <p className="text-sm leading-6 text-[#34413e]">{report.summary}</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <PreviewStat label="Scores" value={report.style_scores.length} />
        <PreviewStat label="Evidence" value={report.evidence.length} />
        <PreviewStat label="Created" value={new Date(report.created_at).toLocaleDateString()} />
      </div>
      {report.evidence.length ? (
        <div className="mt-4 border-t border-[#eef1ec] pt-3">
          <div className="mb-2 text-xs font-semibold text-[#65736f]">Evidence</div>
          <div className="space-y-2">
            {report.evidence.slice(0, 3).map((item, index) => (
              <p
                key={`${item.imported_message_id ?? "evidence"}-${index}`}
                className="border-l-2 border-[#3c7a89] pl-3 text-xs leading-5 text-[#34413e]"
              >
                {item.excerpt}
              </p>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ScoreCard({ score }: { score: PromptIntelligenceReport["style_scores"][number] }) {
  return (
    <article className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-semibold">{score.label}</h3>
          <p className="text-xs text-[#65736f]">{score.verdict}</p>
        </div>
        <div className="text-2xl font-semibold text-[#1e4d45]">{score.score}</div>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[#dfe5dd]">
        <div
          className={cn("h-full rounded-full", scoreClass(score.score))}
          style={{ width: `${score.score}%` }}
        />
      </div>
      <p className="mt-3 text-sm leading-6 text-[#34413e]">{score.explanation}</p>
      <p className="mt-2 text-xs leading-5 text-[#65736f]">{score.improvement}</p>
    </article>
  );
}

function PatternItem({
  pattern,
}: {
  pattern: PromptIntelligenceReport["behavior_patterns"][number];
}) {
  return (
    <article className="border-b border-[#eef1ec] py-3 last:border-0">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">{pattern.title}</h3>
        <span className="rounded-md bg-[#e9f2f6] px-2 py-1 text-[11px] text-[#295061]">
          {Math.round(pattern.confidence * 100)}%
        </span>
      </div>
      <p className="text-sm leading-6 text-[#34413e]">{pattern.detail}</p>
    </article>
  );
}

function RecommendationItem({
  item,
}: {
  item: PromptIntelligenceReport["recommendations"][number];
}) {
  return (
    <article className="border-b border-[#eef1ec] py-3 last:border-0">
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold">{item.title}</h3>
        <span className={priorityClass(item.priority)}>{item.priority}</span>
      </div>
      <p className="text-sm leading-6 text-[#34413e]">{item.detail}</p>
      {item.example_rewrite ? (
        <p className="mt-2 rounded-md bg-[#fbfcf7] px-3 py-2 text-xs leading-5 text-[#34413e]">
          {item.example_rewrite}
        </p>
      ) : null}
    </article>
  );
}

function ImportLedger({
  imports,
  analyzing,
  onJudge,
}: {
  imports: ConversationImport[];
  analyzing: boolean;
  onJudge: (item: ConversationImport) => void;
}) {
  return (
    <section className="rounded-md border border-[#d9ded2] bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-[#eef1ec] px-4 py-3">
        <Database className="size-4 text-[#1e4d45]" />
        <h2 className="text-sm font-semibold">Import Ledger</h2>
      </div>
      <div className="divide-y divide-[#eef1ec]">
        {imports.length ? (
          imports.slice(0, 6).map((item) => (
            <div
              key={item.id}
              className="grid gap-3 px-4 py-3 text-sm md:grid-cols-[minmax(0,1fr)_auto]"
            >
              <div className="min-w-0">
                <div className="font-medium">{item.title || "Untitled import"}</div>
                <div className="mt-1 flex flex-wrap gap-2 text-xs text-[#65736f]">
                  <span>{item.platform}</span>
                  <span>{item.source_type}</span>
                  <span>{item.message_count} messages</span>
                  <span>{item.redaction_status}</span>
                </div>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={analyzing}
                onClick={() => onJudge(item)}
              >
                <SearchCheck />
                Judge
              </Button>
            </div>
          ))
        ) : (
          <p className="px-4 py-6 text-sm text-[#65736f]">No imports yet.</p>
        )}
      </div>
    </section>
  );
}

function ReportHistory({
  reports,
  selectedId,
  onSelect,
}: {
  reports: PromptIntelligenceReport[];
  selectedId: string | null;
  onSelect: (report: PromptIntelligenceReport) => void;
}) {
  return (
    <section className="rounded-md border border-[#d9ded2] bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-[#eef1ec] px-4 py-3">
        <FileText className="size-4 text-[#1e4d45]" />
        <h2 className="text-sm font-semibold">Report History</h2>
      </div>
      <div className="divide-y divide-[#eef1ec]">
        {reports.length ? (
          reports.slice(0, 8).map((item) => (
            <button
              key={item.id}
              type="button"
              className={cn(
                "block w-full px-4 py-3 text-left text-sm hover:bg-[#fbfcf7]",
                selectedId === item.id ? "bg-[#edf1e8]" : "bg-white",
              )}
              onClick={() => onSelect(item)}
            >
              <div className="line-clamp-2 font-medium">{item.headline}</div>
              <div className="mt-1 text-xs text-[#65736f]">
                {new Date(item.created_at).toLocaleString()}
              </div>
            </button>
          ))
        ) : (
          <p className="px-4 py-6 text-sm text-[#65736f]">No reports yet.</p>
        )}
      </div>
    </section>
  );
}

function Panel({
  title,
  icon,
  children,
}: {
  title: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="rounded-md border border-[#d9ded2] bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-[#eef1ec] px-4 py-3 text-[#1e4d45]">
        {icon}
        <h2 className="text-sm font-semibold text-[#1d2523]">{title}</h2>
      </div>
      <div className="px-4 py-1">{children}</div>
    </section>
  );
}

function Metric({
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
      <div className="truncate text-2xl font-semibold">{value}</div>
      <div className="text-xs text-[#65736f]">{label}</div>
    </div>
  );
}

function MiniSignal({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#eef1ec] px-3 py-2">
      <div className="text-xs text-[#65736f]">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}

function PreviewStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md bg-[#fbfcf7] px-3 py-2">
      <div className="truncate text-sm font-semibold text-[#1e4d45]">{value}</div>
      <div className="text-xs text-[#65736f]">{label}</div>
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="block space-y-1 text-xs font-medium text-[#34413e]">
      <span>{label}</span>
      <select
        className="h-9 w-full rounded-md border border-[#cbd5cd] bg-white px-2 text-sm outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function scoreClass(score: number) {
  if (score >= 78) {
    return "bg-[#1e4d45]";
  }
  if (score >= 58) {
    return "bg-[#3c7a89]";
  }
  if (score >= 38) {
    return "bg-amber-500";
  }
  return "bg-rose-500";
}

function priorityClass(priority: PromptIntelligenceReport["recommendations"][number]["priority"]) {
  return cn(
    "rounded-md px-2 py-1 text-[11px] font-medium",
    priority === "high"
      ? "bg-rose-100 text-rose-800"
      : priority === "medium"
        ? "bg-amber-100 text-amber-800"
        : "bg-[#e9f2f6] text-[#295061]",
  );
}
