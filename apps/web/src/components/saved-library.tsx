"use client";

import { Copy, Library, Play, Save } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { getSavedPrompts, SavedPrompt } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function SavedLibrary() {
  const [prompts, setPrompts] = useState<SavedPrompt[]>([]);
  const [status, setStatus] = useState("Loading");

  useEffect(() => {
    getSavedPrompts()
      .then((items) => {
        setPrompts(items);
        setStatus(`${items.length} saved`);
      })
      .catch(() => setStatus("Offline"));
  }, []);

  return (
    <main className="min-h-screen bg-[#f6f7f2] text-[#1d2523]">
      <header className="border-b border-[#d9ded2] bg-[#fbfcf7]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-md bg-[#1e4d45] text-white">
              <Library className="size-4" />
            </div>
            <div>
              <h1 className="text-lg font-semibold">Prompt Library</h1>
              <p className="text-xs text-[#65736f]">{status}</p>
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

      <section className="mx-auto grid max-w-6xl gap-3 px-4 py-4 md:grid-cols-2">
        {prompts.length ? (
          prompts.map((prompt) => (
            <article
              className="rounded-md border border-[#d9ded2] bg-white p-4 shadow-sm"
              key={prompt.id}
            >
              <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold">{prompt.label ?? prompt.title}</h2>
                  <p className="text-xs text-[#65736f]">
                    {prompt.strategy.replaceAll("_", " ")}
                  </p>
                </div>
                <div className="flex gap-1">
                  <Button
                    type="button"
                    variant="outline"
                    size="icon-sm"
                    onClick={() => navigator.clipboard.writeText(prompt.prompt_text)}
                    title="Copy prompt"
                  >
                    <Copy />
                  </Button>
                  <Link href={`/sessions/${prompt.session_id}`}>
                    <Button type="button" variant="outline" size="icon-sm" title="Open session">
                      <Play />
                    </Button>
                  </Link>
                </div>
              </div>
              <p className="line-clamp-6 whitespace-pre-wrap text-sm leading-6 text-[#34413e]">
                {prompt.prompt_text}
              </p>
            </article>
          ))
        ) : (
          <div className="rounded-md border border-dashed border-[#c8d2ca] bg-white p-8 text-sm text-[#65736f]">
            <div className="mb-2 flex items-center gap-2 font-medium text-[#1d2523]">
              <Save className="size-4" />
              No saved prompts yet
            </div>
            Saved prompts appear here after using the workspace.
          </div>
        )}
      </section>
    </main>
  );
}
