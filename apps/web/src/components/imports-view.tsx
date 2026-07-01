"use client";

import {
  Brain,
  Database,
  FileText,
  RefreshCw,
  RotateCw,
  ShieldCheck,
  Trash2,
  UploadCloud,
} from "lucide-react";
import type { ReactNode } from "react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import {
  ConversationImport,
  createImport,
  deleteImport,
  getImports,
  ImportPlatform,
  ImportSourceType,
  reprocessImport,
} from "@/lib/api";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const platformOptions: { value: ImportPlatform; label: string }[] = [
  { value: "manual", label: "Manual" },
  { value: "codex", label: "Codex" },
  { value: "claude", label: "Claude" },
  { value: "chatgpt", label: "ChatGPT" },
  { value: "gemini", label: "Gemini" },
  { value: "cursor", label: "Cursor" },
  { value: "windsurf", label: "Windsurf" },
  { value: "generic", label: "Generic" },
];

const sourceOptions: { value: ImportSourceType; label: string }[] = [
  { value: "paste", label: "Paste" },
  { value: "markdown", label: "Markdown" },
  { value: "json", label: "JSON" },
  { value: "text", label: "Text" },
  { value: "manual", label: "Manual" },
];

export function ImportsView() {
  const [imports, setImports] = useState<ConversationImport[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [platform, setPlatform] = useState<ImportPlatform>("manual");
  const [sourceType, setSourceType] = useState<ImportSourceType>("paste");
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [status, setStatus] = useState("Loading");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [busyImportId, setBusyImportId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    loadImports();
  }, []);

  const selectedImport = useMemo(
    () => imports.find((item) => item.id === selectedId) ?? imports[0] ?? null,
    [imports, selectedId],
  );

  async function loadImports() {
    setRefreshing(true);
    setError("");
    try {
      const values = await getImports();
      setImports(values);
      setStatus(values.length ? "Ready" : "Empty");
      setSelectedId((current) => current ?? values[0]?.id ?? null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Imports unavailable");
      setStatus("Offline");
    } finally {
      setRefreshing(false);
    }
  }

  async function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!rawText.trim()) {
      setError("Import text is required");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const created = await createImport({
        platform,
        source_type: sourceType,
        title: title.trim() || null,
        raw_text: rawText,
      });
      setImports((current) => [created, ...current.filter((item) => item.id !== created.id)]);
      setSelectedId(created.id);
      setTitle("");
      setRawText("");
      setStatus("Imported");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Import failed");
    } finally {
      setSaving(false);
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
      setStatus("Loaded file");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "File upload failed");
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function reprocess(item: ConversationImport) {
    setBusyImportId(item.id);
    setError("");
    try {
      const updated = await reprocessImport(item.id);
      setImports((current) =>
        current.map((existing) => (existing.id === updated.id ? updated : existing)),
      );
      setSelectedId(updated.id);
      setStatus("Reprocessed");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Reprocess failed");
    } finally {
      setBusyImportId(null);
    }
  }

  async function remove(item: ConversationImport) {
    setBusyImportId(item.id);
    setError("");
    try {
      await deleteImport(item.id);
      setImports((current) => current.filter((existing) => existing.id !== item.id));
      setSelectedId((current) => (current === item.id ? null : current));
      setStatus("Deleted");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Delete failed");
    } finally {
      setBusyImportId(null);
    }
  }

  return (
    <AppShell
      title="Prompt Imports"
      status={status}
      icon={<Database className="size-4" />}
      actions={
        <Button type="button" variant="outline" onClick={loadImports} disabled={refreshing}>
          <RefreshCw className={cn(refreshing ? "animate-spin" : "")} />
          Refresh
        </Button>
      }
    >
      <div className="mx-auto grid max-w-6xl gap-4 px-4 py-4 lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        {error ? (
          <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800 lg:col-span-2">
            {error}
          </p>
        ) : null}

        <section className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <UploadCloud className="size-4 text-[#1e4d45]" />
            <h2 className="text-sm font-semibold">New Prompt Session</h2>
          </div>
          <form className="space-y-3" onSubmit={submitImport}>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="space-y-1 text-xs font-medium text-[#34413e]">
                <span>Platform</span>
                <select
                  className="h-9 w-full rounded-md border border-[#cbd5cd] bg-white px-2 text-sm outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
                  value={platform}
                  onChange={(event) => setPlatform(event.target.value as ImportPlatform)}
                >
                  {platformOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-1 text-xs font-medium text-[#34413e]">
                <span>Source</span>
                <select
                  className="h-9 w-full rounded-md border border-[#cbd5cd] bg-white px-2 text-sm outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
                  value={sourceType}
                  onChange={(event) => setSourceType(event.target.value as ImportSourceType)}
                >
                  {sourceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="space-y-1 text-xs font-medium text-[#34413e]">
              <span>Title</span>
              <input
                className="h-9 w-full rounded-md border border-[#cbd5cd] bg-white px-2 text-sm outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Conversation title"
              />
            </label>
            <label className="space-y-1 text-xs font-medium text-[#34413e]">
              <span>Transcript</span>
              <textarea
                className="min-h-64 w-full resize-y rounded-md border border-[#cbd5cd] bg-white p-3 text-sm leading-6 outline-none focus:border-[#1e4d45] focus:ring-2 focus:ring-[#b8d3ca]"
                value={rawText}
                onChange={(event) => setRawText(event.target.value)}
                placeholder="User: ..."
              />
            </label>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-xs text-[#65736f]">
                <ShieldCheck className="size-4 text-[#1e4d45]" />
                {rawText.length.toLocaleString()} chars
              </div>
              <div className="flex flex-wrap gap-2">
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
                <Button type="submit" disabled={saving}>
                  <UploadCloud />
                  {saving ? "Importing" : "Import"}
                </Button>
              </div>
            </div>
          </form>
        </section>

        <section className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric icon={<Database className="size-4" />} label="Imports" value={imports.length} />
            <Metric
              icon={<FileText className="size-4" />}
              label="Messages"
              value={imports.reduce((sum, item) => sum + item.message_count, 0)}
            />
            <Metric
              icon={<ShieldCheck className="size-4" />}
              label="Redacted"
              value={imports.filter((item) => item.redaction_status === "redacted").length}
            />
          </div>

          <div className="rounded-md border border-[#d9ded2] bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-[#eef1ec] px-4 py-3">
              <div className="flex items-center gap-2">
                <Brain className="size-4 text-[#1e4d45]" />
                <h2 className="text-sm font-semibold">Import Ledger</h2>
              </div>
              <span className="text-xs text-[#65736f]">{imports.length} total</span>
            </div>
            {imports.length ? (
              <div className="max-h-80 overflow-auto">
                {imports.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    className={cn(
                      "block w-full border-b border-[#eef1ec] px-4 py-3 text-left text-sm hover:bg-[#fbfcf7]",
                      selectedImport?.id === item.id ? "bg-[#edf1e8]" : "bg-white",
                    )}
                    onClick={() => setSelectedId(item.id)}
                  >
                    <div className="mb-1 flex items-start justify-between gap-3">
                      <span className="font-medium">{item.title || "Untitled import"}</span>
                      <span className={redactionClass(item.redaction_status)}>
                        {item.redaction_status}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs text-[#65736f]">
                      <span>{item.platform}</span>
                      <span>{item.source_type}</span>
                      <span>{item.message_count} messages</span>
                      <span>{new Date(item.created_at).toLocaleString()}</span>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="px-4 py-8 text-sm text-[#65736f]">No imports yet.</div>
            )}
          </div>
        </section>

        <section className="rounded-md border border-[#d9ded2] bg-white shadow-sm lg:col-span-2">
          <div className="flex flex-col gap-3 border-b border-[#eef1ec] px-4 py-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-sm font-semibold">
                {selectedImport?.title || "Import Preview"}
              </h2>
              <p className="text-xs text-[#65736f]">
                {selectedImport
                  ? `${selectedImport.platform} / ${selectedImport.source_type}`
                  : "No import selected"}
              </p>
            </div>
            {selectedImport ? (
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => reprocess(selectedImport)}
                  disabled={busyImportId === selectedImport.id}
                  title="Reprocess import"
                >
                  <RotateCw className={cn(busyImportId === selectedImport.id ? "animate-spin" : "")} />
                  Reprocess
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  onClick={() => remove(selectedImport)}
                  disabled={busyImportId === selectedImport.id}
                  title="Delete import"
                >
                  <Trash2 />
                  Delete
                </Button>
              </div>
            ) : null}
          </div>
          {selectedImport ? (
            <div>
              <div className="grid gap-3 border-b border-[#eef1ec] px-4 py-3 text-sm sm:grid-cols-4">
                <PreviewStat label="Conversations" value={selectedImport.conversation_count} />
                <PreviewStat label="Messages" value={selectedImport.message_count} />
                <PreviewStat
                  label="Redactions"
                  value={selectedImport.import_metadata.redaction_count ?? 0}
                />
                <PreviewStat
                  label="Format"
                  value={selectedImport.import_metadata.input_format ?? selectedImport.source_type}
                />
              </div>
              <div className="max-h-[34rem] overflow-auto">
                {selectedImport.conversations.map((conversation) => (
                  <div key={conversation.id}>
                    <div className="border-b border-[#eef1ec] bg-[#fbfcf7] px-4 py-2 text-xs font-medium text-[#65736f]">
                      {conversation.title || "Conversation"} / {conversation.message_count} messages
                    </div>
                    {conversation.messages.map((message) => (
                      <div
                        key={message.id}
                        className="grid gap-2 border-b border-[#eef1ec] px-4 py-3 text-sm md:grid-cols-[8rem_minmax(0,1fr)]"
                      >
                        <div className="flex items-center gap-2 text-xs font-medium text-[#65736f]">
                          <span className="rounded-md bg-[#edf1e8] px-2 py-1">
                            {message.role}
                          </span>
                          {message.redacted ? (
                            <span className="rounded-md bg-amber-100 px-2 py-1 text-amber-800">
                              redacted
                            </span>
                          ) : null}
                        </div>
                        <p className="whitespace-pre-wrap break-words leading-6 text-[#34413e]">
                          {message.text}
                        </p>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="px-4 py-8 text-sm text-[#65736f]">No preview available.</div>
          )}
        </section>
      </div>
    </AppShell>
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
    <div className="rounded-md border border-[#d9ded2] bg-white p-3 shadow-sm">
      <div className="mb-2 flex items-center gap-2 text-[#1e4d45]">{icon}</div>
      <div className="text-xl font-semibold">{value}</div>
      <div className="text-xs text-[#65736f]">{label}</div>
    </div>
  );
}

function PreviewStat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <div className="text-lg font-semibold text-[#1e4d45]">{value}</div>
      <div className="text-xs text-[#65736f]">{label}</div>
    </div>
  );
}

function redactionClass(status: string) {
  return cn(
    "rounded-md px-2 py-1 text-[11px] font-medium",
    status === "redacted"
      ? "bg-amber-100 text-amber-800"
      : "bg-[#dbebe0] text-[#214b40]",
  );
}
