export type PromptSettings = {
  length: "short" | "medium" | "deep";
  skill_level: "beginner" | "practical" | "expert";
  tone: "direct" | "friendly" | "technical";
  format: "checklist" | "guide" | "table" | "conversation" | "plan";
  risk: "safe_only" | "normal" | "advanced";
  sources: "none" | "web" | "official_docs";
  target_platform:
    | "codex"
    | "claude"
    | "chatgpt"
    | "gemini"
    | "cursor"
    | "grok"
    | "perplexity"
    | "copilot"
    | "generic"
    | "other";
  detail_level: "concise" | "balanced" | "exhaustive";
  formality: "casual" | "neutral" | "formal";
  temperature: "precise" | "balanced" | "creative";
  reasoning_style: "direct_answer" | "step_by_step" | "ask_first" | "explore_options";
  source_strictness: "none" | "cite_when_needed" | "official_only" | "evidence_first";
  interaction_mode: "one_shot" | "iterative" | "agentic";
};

export type RefinementMode = "refinement" | "quick";
export type ClarifyingQuestionState = "unanswered" | "answered" | "skipped";
export type SessionAiPlatform =
  | "chatgpt"
  | "claude"
  | "grok"
  | "perplexity"
  | "gemini"
  | "copilot"
  | "cursor"
  | "codex"
  | "other";

export type ActiveSessionProfile = {
  display_name: string;
  primary_ai_platform: SessionAiPlatform;
  rules_accepted: boolean;
  started_at: string;
};

export type SessionResponse = {
  id: string;
  display_name: string | null;
  primary_ai_platform: string | null;
  rules_accepted: boolean;
  session_metadata: Record<string, unknown>;
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
  ended_at: string | null;
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
  answer: string | null;
  state: ClarifyingQuestionState;
  revision_count: number;
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
  platform_fit_rating: number | null;
  platform_fit_breakdown: Record<string, number>;
  recommendation_summary: string | null;
  why_this_variant: string | null;
  assumption_notes: string[];
  modification_audit_trail: {
    id: string;
    label: string;
    reason: string;
    source: string;
  }[];
  rules_matched: {
    id: string;
    label: string;
    matched: boolean;
    detail: string;
  }[];
  user_trait_alignment: {
    trait_key?: string;
    label?: string;
    score?: number;
    confidence?: number;
    used_for?: string;
  }[];
  optimization_paths: {
    id: string;
    label: string;
    detail: string;
  }[];
  recommended_actions: {
    id: string;
    label: string;
    impact: string;
    priority: string;
  }[];
  scorer_metadata: Record<string, unknown>;
  created_at: string;
};

export type PipelineResponse = {
  session_id: string;
  mode: RefinementMode;
  classification: ClassificationResponse;
  needs_clarification: boolean;
  questions: ClarifyingQuestion[];
  prompts: PromptVariant[];
  recommended_prompt_id: string | null;
  assumptions: string[];
  revisions: PromptRevision[];
  timeline: string[];
  stage_timings_ms: Record<string, number>;
  guardrail_status: "passed" | "blocked";
  guardrail_message: string | null;
  safe_redirect: string | null;
};

export type PromptRevision = {
  id: string;
  session_id: string | null;
  prompt_variant_id: string | null;
  revision_type: string;
  before_text: string | null;
  after_text: string;
  rationale: string | null;
  revision_metadata: Record<string, unknown>;
  created_at: string;
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
  user_corrected: boolean;
  user_note: string | null;
  created_at: string;
  updated_at: string;
};

export type ProfileEvidenceReference = {
  type: string;
  label: string;
  excerpt?: string | null;
  session_id?: string | null;
  imported_message_id?: string | null;
  trait_key?: string | null;
  confidence?: number | null;
};

export type ProfileInsightItem = {
  title: string;
  detail: string;
  confidence: number;
  evidence: ProfileEvidenceReference[];
  action?: string | null;
};

export type ProfileInsights = {
  profile_status: string;
  headline: string;
  common_missing_details: ProfileInsightItem[];
  preferences: ProfileInsightItem[];
  frequent_domains: ProfileInsightItem[];
  platform_advice: ProfileInsightItem[];
  recent_revisions: ProfileInsightItem[];
  suggested_questions: string[];
  empty_state?: string | null;
};

export type ProfileQuestionResponse = {
  question: string;
  answer: string;
  confidence: number;
  evidence_level: string;
  evidence: ProfileEvidenceReference[];
  suggested_followups: string[];
  needs_more_evidence: boolean;
};

export type ProfileObservationUpdate = {
  summary?: string | null;
  score?: number | null;
  note?: string | null;
};

export type ProfileObservationDeleteResponse = {
  id: string;
  deleted: boolean;
  trait_key: string;
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
  platform_preferences: PlatformPreference[];
  created_at: string;
  updated_at: string;
};

export type PlatformPreference = {
  id: string;
  platform: string;
  preference: Partial<PromptSettings>;
  confidence: number;
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

export type EndSessionResponse = {
  id: string;
  status: string;
  ended_at: string;
};

export type AuditLog = {
  id: string;
  session_id: string | null;
  entity_type: string;
  entity_id: string | null;
  event_type: string;
  event_metadata: Record<string, unknown>;
  created_at: string;
};

export type SessionExport = {
  session_id: string;
  format: "markdown" | "json";
  filename: string;
  content: string;
  metadata: Record<string, unknown>;
};

export type DeleteSessionDataResponse = {
  session_id: string;
  deleted: boolean;
  deleted_counts: Record<string, number>;
};

export type ProfileExport = {
  format: "markdown" | "json";
  filename: string;
  content: string;
  metadata: Record<string, unknown>;
};

export type DeleteProfileDataResponse = {
  deleted: boolean;
  deleted_counts: Record<string, number>;
};

export const defaultSettings: PromptSettings = {
  length: "medium",
  skill_level: "practical",
  tone: "friendly",
  format: "guide",
  risk: "normal",
  sources: "none",
  target_platform: "generic",
  detail_level: "balanced",
  formality: "neutral",
  temperature: "balanced",
  reasoning_style: "ask_first",
  source_strictness: "none",
  interaction_mode: "iterative",
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is required outside local development");
  }
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
  activeSession: ActiveSessionProfile,
) {
  return request<SessionResponse>("/sessions", {
    method: "POST",
    body: JSON.stringify({
      raw_input: rawInput,
      settings,
      display_name: activeSession.display_name,
      primary_ai_platform: activeSession.primary_ai_platform,
      rules_accepted: activeSession.rules_accepted,
      session_metadata: {
        started_at: activeSession.started_at,
        frontend_session_version: "phase14-v1",
      },
    }),
  });
}

export async function getSession(sessionId: string) {
  return request<SessionResponse>(`/sessions/${sessionId}`);
}

export async function endSession(sessionId: string) {
  return request<EndSessionResponse>(`/sessions/${sessionId}/end`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getSessionAuditLogs(sessionId: string) {
  return request<AuditLog[]>(`/sessions/${sessionId}/audit-logs`);
}

export async function exportSession(
  sessionId: string,
  format: "markdown" | "json" = "markdown",
) {
  return request<SessionExport>(`/sessions/${sessionId}/export?format=${format}`);
}

export async function deleteSessionData(sessionId: string) {
  return request<DeleteSessionDataResponse>(`/sessions/${sessionId}/data`, {
    method: "DELETE",
  });
}

export async function runPipeline(
  sessionId: string,
  settings: PromptSettings,
  answers: Record<string, string>,
  questionStates: Record<string, ClarifyingQuestionState> = {},
  mode: RefinementMode = "refinement",
) {
  const questionIds = new Set([
    ...Object.keys(answers),
    ...Object.keys(questionStates),
  ]);
  return request<PipelineResponse>(`/sessions/${sessionId}/run-pipeline`, {
    method: "POST",
    body: JSON.stringify({
      settings,
      mode,
      answers: Array.from(questionIds)
        .map((question_id) => {
          const answer = answers[question_id]?.trim() ?? "";
          const state =
            questionStates[question_id] ??
            (answer.length ? "answered" : "unanswered");
          return {
            question_id,
            answer: state === "skipped" ? null : answer,
            state,
          };
        }),
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

export async function exportProfile(format: "markdown" | "json" = "markdown") {
  return request<ProfileExport>(`/profile/export?format=${format}`);
}

export async function deleteProfileData() {
  return request<DeleteProfileDataResponse>("/profile/data", {
    method: "DELETE",
  });
}

export async function refreshProfile() {
  return request<PromptProfile>("/profile/refresh", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getProfileInsights() {
  return request<ProfileInsights>("/profile/insights");
}

export async function askProfileQuestion(question: string) {
  return request<ProfileQuestionResponse>("/profile/questions", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export async function correctProfileObservation(
  observationId: string,
  payload: ProfileObservationUpdate,
) {
  return request<PromptProfile>(`/profile/observations/${observationId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteProfileObservation(observationId: string) {
  return request<ProfileObservationDeleteResponse>(
    `/profile/observations/${observationId}`,
    {
      method: "DELETE",
    },
  );
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
