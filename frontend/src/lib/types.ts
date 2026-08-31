export type Role = "admin" | "gov_officer" | "training_provider" | "beneficiary";

export interface UserPublic {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  phone?: string | null;
  organisation?: string | null;
  district?: string | null;
  is_active: boolean;
  is_email_verified: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserPublic;
}

export interface PageMeta {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
export interface Paginated<T> {
  items: T[];
  meta: PageMeta;
}

export interface Location {
  id: string;
  state: string;
  district: string;
  block?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  population?: number | null;
  sc_population?: number | null;
}

export interface Beneficiary {
  id: string;
  full_name: string;
  age?: number | null;
  gender: string;
  phone?: string | null;
  preferred_language: string;
  social_category: string;
  pmajay_id?: string | null;
  location_id?: string | null;
  village?: string | null;
  address?: string | null;
  education_level: string;
  education_notes?: string | null;
  current_occupation?: string | null;
  family_occupation?: string | null;
  monthly_income?: number | null;
  skills: string[];
  interests: string[];
  constraints: string[];
  mobility: string;
  employment_preference: string;
  has_smartphone: boolean;
  has_bank_account: boolean;
  status: string;
  ai_profile?: Record<string, unknown> | null;
  is_demo: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  location?: Location | null;
  district?: string | null;
}

export interface Skill {
  id: string;
  name: string;
  code?: string | null;
  sector: string;
  description?: string | null;
  nsqf_level: number;
  min_education: string;
  min_age: number;
  max_age?: number | null;
  typical_duration_hours: number;
  avg_wage_monthly?: number | null;
  self_employable: boolean;
  tags: string[];
  prerequisites: string[];
  demand_index: number;
  is_simulated: boolean;
}

export interface NsqfRole {
  id: string;
  title: string;
  nco_code?: string | null;
  qp_code?: string | null;
  sector: string;
  nsqf_level: number;
  description?: string | null;
  eligibility?: string | null;
  entry_wage_monthly?: number | null;
  growth_outlook: string;
  self_employment_path?: string | null;
  skills: Skill[];
}

export interface TrainingProgram {
  id: string;
  title: string;
  provider_id: string;
  skill_id: string;
  nsqf_level: number;
  mode: string;
  duration_hours: number;
  duration_weeks: number;
  total_seats: number;
  filled_seats: number;
  seats_available: number;
  fee: number;
  stipend_monthly: number;
  is_residential: boolean;
  start_date?: string | null;
  end_date?: string | null;
  application_deadline?: string | null;
  eligibility_min_education: string;
  eligibility_min_age: number;
  eligibility_max_age?: number | null;
  eligibility_notes: string[];
  status: string;
  certification_body?: string | null;
  skill?: Skill | null;
  provider?: { id: string; name: string; type: string; rating: number; location?: Location | null } | null;
  location?: Location | null;
}

export interface InterviewMessage {
  id: string;
  sequence: number;
  role: "system" | "assistant" | "user";
  language: string;
  text_original?: string | null;
  text_english?: string | null;
  audio_url?: string | null;
  stt_confidence?: number | null;
  intent?: string | null;
  entities: Record<string, unknown>;
  created_at: string;
}

export interface Interview {
  id: string;
  beneficiary_id: string;
  language: string;
  channel: string;
  status: string;
  current_step: number;
  total_steps: number;
  completion_pct: number;
  transcript?: string | null;
  extracted_entities: Record<string, unknown>;
  structured_profile?: Record<string, unknown> | null;
  stt_provider: string;
  llm_provider: string;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
  messages: InterviewMessage[];
}

export interface Recommendation {
  id: string;
  beneficiary_id: string;
  rank: number;
  match_score: number;
  factor_scores: Record<string, number>;
  reasons: string[];
  skill_gaps: string[];
  career_pathway: { step: number; title: string; detail: string }[];
  engine_version: string;
  is_accepted?: boolean | null;
  is_demo: boolean;
  created_at: string;
  skill?: Skill | null;
  nsqf_role?: NsqfRole | null;
  suggested_program?: TrainingProgram | null;
}

export interface Application {
  id: string;
  beneficiary_id: string;
  program_id: string;
  recommendation_id?: string | null;
  status: string;
  eligibility_passed: boolean;
  eligibility_report: { passed: boolean; checks: { criterion: string; required: unknown; actual: unknown; passed: boolean }[] };
  progress_pct: number;
  attendance_pct: number;
  assessment_score?: number | null;
  certificate_number?: string | null;
  certificate_url?: string | null;
  submitted_at?: string | null;
  enrolled_at?: string | null;
  completed_at?: string | null;
  notes?: string | null;
  is_demo: boolean;
  created_at: string;
  program?: TrainingProgram | null;
}

export interface Outcome {
  id: string;
  beneficiary_id: string;
  stage: string;
  outcome_type?: string | null;
  occurred_on?: string | null;
  employer_or_venture?: string | null;
  sector?: string | null;
  district?: string | null;
  income_before?: number | null;
  income_after?: number | null;
  income_delta_pct?: number | null;
  is_verified: boolean;
  is_demo: boolean;
  created_at: string;
}

export interface KpiCard {
  key: string;
  label: string;
  value: number;
  unit: string;
  delta_pct?: number | null;
  trend: number[];
}
export interface Overview {
  generated_at: string;
  kpis: KpiCard[];
  funnel: { stage: string; count: number; conversion_from_previous: number }[];
  district_stats: DistrictStat[];
  skill_demand: SkillDemandStat[];
  enrollment_trend: { period: string; value: number }[];
  language_split: Record<string, number>;
  recommendation_success_rate: number;
  notes: string;
}
export interface DistrictStat {
  district: string;
  state: string;
  beneficiaries: number;
  interviews_done: number;
  recommendations: number;
  in_training: number;
  certified: number;
  placed: number;
  self_employed: number;
  placement_rate: number;
}
export interface SkillDemandStat {
  skill: string;
  sector: string;
  demand_score: number;
  supply_score: number;
  gap_score: number;
  open_positions: number;
}
export interface OutcomeDashboard {
  completion_rate: number;
  placement_rate: number;
  self_employment_rate: number;
  wage_employment_rate: number;
  avg_income_before: number;
  avg_income_after: number;
  avg_income_improvement_pct: number;
  district_performance: DistrictStat[];
  demand_vs_supply: SkillDemandStat[];
}

export interface MapPoint {
  location_id: string;
  state: string;
  district: string;
  latitude?: number | null;
  longitude?: number | null;
  beneficiaries: number;
  interviews_done: number;
  in_training: number;
  certified: number;
  placed: number;
  training_centers: number;
  open_opportunities: number;
  top_demand_skills: string[];
  top_gap_skills: string[];
  avg_demand_score: number;
  avg_supply_score: number;
  avg_gap_score: number;
}
export interface MapResponse {
  period: string;
  points: MapPoint[];
  totals: Record<string, number>;
}

export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "alert";
  title: string;
  body?: string | null;
  link?: string | null;
  meta: Record<string, unknown>;
  is_read: boolean;
  read_at?: string | null;
  created_at: string;
}

export interface AppConfig {
  project_name: string;
  env: string;
  api_prefix: string;
  languages: { code: string; label: string }[];
  roles: Role[];
  ai: { stt: string; tts: string; translate: string; llm: string; mock_mode: boolean };
  supabase_configured: boolean;
}
