import { PromptWorkspace } from "@/components/prompt-workspace";

export default async function ComparePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <PromptWorkspace initialSessionId={id === "new" ? undefined : id} initialCompare />;
}
