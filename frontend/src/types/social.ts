export interface PostAttachment {
  id: string;
  file_url: string;
  file_type: string;
  created_at?: string;
}

export interface PostComment {
  id: string;
  author_id: string;
  author_name?: string;
  author_specialty?: string;
  author_institution?: string;
  author_credentials?: string;
  content: string;
  created_at: string;
}

export interface TreatmentSuggestion {
  id: string;
  post_id: string;
  author_id: string;
  author_name: string;
  author_specialty: string;
  author_institution?: string;
  author_credentials?: string;
  drug_or_intervention: string;
  dosage_and_route?: string;
  clinical_rationale: string;
  evidence_grade?: string;
  endorsements_count: number;
  is_adopted: boolean;
  created_at: string;
}

export interface PollOption {
  label: string;
  votes: number;
}

export interface PollData {
  question: string;
  options: PollOption[];
  total_votes: number;
  has_voted?: boolean;
  voted_index?: number | null;
}

export interface QuotedPostSummary {
  id: string;
  author_name: string;
  author_specialty?: string;
  author_institution?: string;
  disease_name: string;
  diagnosis: string;
  clinical_findings: string;
  created_at: string;
  is_urgent_consult?: boolean;
}

export interface DoctorPost {
  id: string;
  author_id: string;
  author_name?: string;
  author_specialty?: string;
  author_institution?: string;
  author_credentials?: string;
  is_author_verified?: boolean;
  case_status?: string; // "urgent_consult" | "solved" | "active"
  is_urgent_consult?: boolean;
  is_emergency?: boolean;
  is_solved?: boolean;
  patient_outcome?: string | null;
  outcome_reported_at?: string | null;
  author_country?: string;
  author_license_body?: string;
  disease_name: string;
  clinical_findings: string;
  diagnosis: string;
  treatment_plan: string;
  drugs_used: string[];
  specialty_tags: string[];
  tags?: string[];
  likes_count: number;
  comments_count: number;
  suggestions_count?: number;
  is_liked_by_me: boolean;
  is_bookmarked_by_me: boolean;
  bookmark_folder?: string;
  endorsements_count?: number;
  is_endorsed_by_me?: boolean;
  reactions_breakdown?: Record<string, number>;
  my_reaction?: string | null;
  poll_data?: PollData | null;
  ai_knowledge_weight?: number;
  created_at: string;
  attachments: PostAttachment[];
  comments: PostComment[];
  treatment_suggestions?: TreatmentSuggestion[];
  quoted_post_id?: string | null;
  quoted_post?: QuotedPostSummary | null;
}

export interface CurbsideMessage {
  id: string;
  post_id: string;
  sender_id: string;
  sender_name: string;
  sender_specialty: string;
  receiver_id: string;
  content: string;
  created_at: string;
  is_read?: boolean;
}


export interface TrendingHashtag {
  tag: string;
  count: number;
  has_urgent?: boolean;
}

export interface DoctorProfile {
  id: string;
  full_name?: string;
  name?: string;
  specialization?: string;
  specialty?: string;
  verification_status?: string;
  license_verification?: string;
  institution?: string;
  bio?: string;
  avatar_url?: string;
  is_verified?: boolean;
  reputation_score?: number;
  country?: string;
  post_count?: number;
  cases_count?: number;
  suggestions_count?: number;
  endorsements_count?: number;
  followers_count?: number;
  is_following?: boolean;
}

export interface DoctorMyStats {
  cases_count: number;
  endorsements_count: number;
  validations_count: number;
  consensus_rate: number;
  followers_count: number;
}

