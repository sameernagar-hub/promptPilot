export type PromptSettings = {
  length: "short" | "medium" | "deep";
  skill_level: "beginner" | "practical" | "expert";
  tone: "direct" | "friendly" | "technical";
  format: "checklist" | "guide" | "table" | "conversation" | "plan";
  risk: "safe_only" | "normal" | "advanced";
  sources: "none" | "web" | "official_docs";
};

export type SessionResponse = {
  id: string;
  raw_input: string;
  detected_domain: string | null;
  detected_intent: string | null;
  risk_level: string | null;
  user_settings: PromptSettings;
  status: string;
  clarifying_questions: ClarifyingQuestion[];
  answers: Record<string, string>;
  prompt_variant_ids: string[];
  created_at: string;
  updated_at: string;
};

export type ClassificationResponse = {
  domain: string;
  primary_domain: string | null;
  subdomain: string | null;
  intent: string;
  risk_level: string;
  confidence: number;
  signals: string[];
  evidence: {
    type: string;
    label: string;
    signals: string[];
  }[];
  alternative_domains: string[];
  needs_domain_confirmation: boolean;
  confirmed_domain: string | null;
  domain_source: "detected" | "user_confirmed" | "user_corrected";
};

export type ClarifyingQuestion = {
  id: string;
  question: string;
  reason: string;
  required: boolean;
};

export type PromptVariant = {
  id: string;
  session_id: string;
  title: string;
  strategy: string;
  prompt_text: string;
  recommendation_label: string;
  score_total: number | null;
  score_breakdown: Record<string, number>;
  explanation: string | null;
  created_at: string;
};

export type PipelineResponse = {
  session_id: string;
  classification: ClassificationResponse;
  needs_clarification: boolean;
  questions: ClarifyingQuestion[];
  prompts: PromptVariant[];
  recommended_prompt_id: string | null;
  timeline: string[];
};

export type RunPromptResponse = {
  prompt_id: string;
  provider: string;
  model: string;
  output: string;
};

export type SavedPrompt = {
  id: string;
  prompt_id: string;
  session_id: string;
  title: string;
  prompt_text: string;
  strategy: string;
  label: string | null;
  created_at: string;
};

export type TraitObservation = {
  id: string;
  trait_key: string;
  trait_label: string;
  category: string;
  score: number;
  confidence: number;
  evidence_level: "none" | "tentative" | "emerging" | "strong";
  signal_count: number;
  summary: string;
  evidence: {
    type: string;
    session_id?: string;
    imported_message_id?: string;
    excerpt?: string;
    domain?: string | null;
    intent?: string | null;
    risk_level?: string | null;
    created_at?: string;
  }[];
  signals: {
    id: string;
    trait_key: string;
    signal_key: string;
    signal_label: string;
    score: number;
    weight: number;
    confidence: number;
    explanation: string;
    evidence: {
      type?: string;
      session_id?: string;
      imported_message_id?: string;
      excerpt?: string;
      domain?: string | null;
      intent?: string | null;
      risk_level?: string | null;
      source_ref?: string;
    };
    source_type: string;
    source_ref: string | null;
    created_at: string;
  }[];
  source_type: string;
  source_ref: string | null;
  created_at: string;
  updated_at: string;
};

export type PromptProfile = {
  id: string;
  profile_key: string;
  display_name: string;
  status: "empty" | "partial" | "populated";
  summary: {
    headline?: string;
    session_count?: number;
    import_count?: number;
    imported_message_count?: number;
    signal_count?: number;
    strongest_traits?: {
      trait_key: string;
      score: number;
      confidence: number;
    }[];
    needs_more_evidence?: boolean;
  };
  total_sessions: number;
  total_imports: number;
  observation_count: number;
  last_refreshed_at: string | null;
  traits: TraitObservation[];
  created_at: string;
  updated_at: string;
};

export type ImportPlatform =
  | "manual"
  | "codex"
  | "claude"
  | "chatgpt"
  | "gemini"
  | "cursor"
  | "windsurf"
  | "generic";

export type ImportSourceType = "paste" | "markdown" | "json" | "text" | "manual";

export type ConversationImportRequest = {
  platform: ImportPlatform;
  source_type: ImportSourceType;
  title?: string | null;
  raw_text: string;
};

export type ImportedMessage = {
  id: string;
  role: string;
  text: string;
  redacted: boolean;
  position: number;
  message_timestamp: string | null;
  created_at: string;
};

export type ImportedConversation = {
  id: string;
  import_id: string;
  platform: string;
  external_conversation_id: string | null;
  title: string | null;
  message_count: number;
  messages: ImportedMessage[];
  created_at: string;
  updated_at: string;
};

export type ConversationImport = {
  id: string;
  profile_id: string;
  platform: string;
  source_type: string;
  title: string | null;
  consent_status: string;
  redaction_status: "clean" | "redacted" | "pending" | string;
  conversation_count: number;
  message_count: number;
  import_metadata: {
    normalizer_version?: string;
    input_format?: string;
    redaction_count?: number;
    redaction_types?: string[];
    message_count?: number;
  };
  conversations: ImportedConversation[];
  created_at: string;
  updated_at: string;
};

export type DomainConfirmationResponse = {
  session_id: string;
  classification: ClassificationResponse;
};

export const defaultSettings: PromptSettings = {
  length: "medium",
  skill_level: "practical",
  tone: "friendly",
  format: "guide",
  risk: "normal",
  sources: "none",
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function getHealth() {
  return request<{
    service: string;
    status: string;
    database: { status: string; database?: string; user?: string };
    model_provider: string;
    default_model: string;
  }>("/health");
}

export async function createSession(
  rawInput: string,
  settings: PromptSettings,
) {
  return request<SessionResponse>("/sessions", {
    method: "POST",
    body: JSON.stringify({
      raw_input: rawInput,
      settings,
    }),
  });
}

export async function getSession(sessionId: string) {
  return request<SessionResponse>(`/sessions/${sessionId}`);
}

export async function runPipeline(
  sessionId: string,
  settings: PromptSettings,
  answers: Record<string, string>,
) {
  return request<PipelineResponse>(`/sessions/${sessionId}/run-pipeline`, {
    method: "POST",
    body: JSON.stringify({
      settings,
      answers: Object.entries(answers)
        .filter(([, answer]) => answer.trim().length > 0)
        .map(([question_id, answer]) => ({ question_id, answer })),
    }),
  });
}

export async function confirmDomain(
  sessionId: string,
  confirmedDomain: string,
  accepted: boolean,
) {
  return request<DomainConfirmationResponse>(
    `/sessions/${sessionId}/domain-confirmation`,
    {
      method: "POST",
      body: JSON.stringify({
        confirmed_domain: confirmedDomain,
        accepted,
      }),
    },
  );
}

export async function runPrompt(sessionId: string, promptId: string) {
  return request<RunPromptResponse>(`/sessions/${sessionId}/run-prompt`, {
    method: "POST",
    body: JSON.stringify({ prompt_id: promptId }),
  });
}

export async function savePrompt(promptId: string, label?: string) {
  return request<SavedPrompt>(`/prompts/${promptId}/save`, {
    method: "POST",
    body: JSON.stringify({ label }),
  });
}

export async function getSavedPrompts() {
  return request<SavedPrompt[]>("/saved-prompts");
}

export async function getProfile() {
  return request<PromptProfile>("/profile");
}

export async function refreshProfile() {
  return request<PromptProfile>("/profile/refresh", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getImports() {
  return request<ConversationImport[]>("/imports");
}

export async function createImport(payload: ConversationImportRequest) {
  return request<ConversationImport>("/imports", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function reprocessImport(importId: string) {
  return request<ConversationImport>(`/imports/${importId}/reprocess`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function deleteImport(importId: string) {
  return request<{ id: string; deleted: boolean }>(`/imports/${importId}`, {
    method: "DELETE",
  });
}
