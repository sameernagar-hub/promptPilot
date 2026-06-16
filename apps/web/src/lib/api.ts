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
  intent: string;
  risk_level: string;
  confidence: number;
  signals: string[];
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
    excerpt?: string;
    domain?: string | null;
    intent?: string | null;
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
