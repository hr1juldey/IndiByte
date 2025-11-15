// From LLD Section 2.2.1
export interface UserProfile {
  name: string;
  demographics: {
    age: number;
    gender: "male" | "female" | "other";
    height_cm: number;
    weight_kg: number;
  };
  lifestyle_habits: {
    sleep_hours: number;
    work_style: "desk_job" | "light_activity" | "physical_job";
    exercise_frequency: "rarely" | "1-2_times_week" | "3-4_times_week" | "5_times_week" | "daily";
    commute_type: "car" | "public_transport" | "bike" | "walk";
    smoking: "yes" | "no" | "occasionally";
    alcohol: "none" | "light" | "moderate" | "heavy";
    stress_level: "low" | "moderate" | "high";
  };
  health_metrics: {
    bmi: number;
    bmi_category: "underweight" | "normal" | "overweight" | "obese";
    bmr: number;
    tdee: number;
    daily_energy_target: number;
    health_risks: string[];
  };
  goals: {
    primary_goal: "lose_weight" | "maintain_weight" | "gain_muscle";
    target_weight_kg: number | null;
    timeline_weeks: number | null;
  };
  food_preferences: {
    cuisine_preferences: string[];
    dietary_restrictions: string[];
    allergens: string[];
    disliked_ingredients: string[];
  };
  daily_targets: {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g: number;
    sugar_g: number;
    sodium_mg: number;
  };
  created_at: string;
  last_updated: string;
}

// From LLD Section 2.7 - CitationSource
export interface CitationSource {
  citation_number: number;
  source_type: "openfoodfacts" | "searxng_web" | "health_guideline" | "user_profile";
  title: string;
  url: string | null;
  authority_score: number;
  snippet: string | null;
  accessed_at: string;
}

// From LLD Section 2.7 - DetailedAssessment
export interface DetailedAssessment {
  scan_id: string;
  timestamp: string;
  product_name: string;
  brand: string | null;
  final_score: number;
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  verdict_emoji: string;
  base_score: number;
  context_adjustment: string;
  time_multiplier: number;
  final_calculation: string;
  highlights: string[];
  warnings: string[];
  allergen_alerts: string[];
  moderation_message: string;
  timing_recommendation: string;
  reasoning_steps: string[];
  confidence: number;
  sources: CitationSource[];
  inline_citations: Record<string, number>;
  alternative_products: string[];
  portion_suggestion: string | null;
  nutrition_snapshot: Record<string, any>;
}

// From LLD Section 2.7 - ShortAssessment
export interface ShortAssessment {
  scan_id: string;
  timestamp: string;
  product_name: string;
  final_score: number;
  verdict: "excellent" | "good" | "moderate" | "caution" | "avoid";
  verdict_emoji: string;
  summary: string;
  key_points: string[];
  allergen_alerts: string[];
  main_recommendation: string | null;
}

// From LLD Section 2.8 - OnboardingQuestionEvent
export interface OnboardingQuestionEvent {
  question_number: number;
  total_questions: number;
  category: string;
  question: string;
  response_type: "text" | "choice" | "number";
  choices?: string[];
  validation: Record<string, any>;
  can_skip: boolean;
  progress: number;
}

// From LLD Section 2.8 - OnboardingResponse
export interface OnboardingResponse {
  question_number: number;
  response: string;
}

// From LLD Section 2.8 - ScanProgressEvent
export interface ScanProgressEvent {
  scan_id: string;
  stage: "image_processing" | "nutrition_retrieval" | "profile_loading" | "scoring" | "assessment_generation";
  stage_number: number;
  total_stages: number;
  message: string;
  progress: number;
}

// From LLD Section 2.8 - ScanErrorEvent
export interface ScanErrorEvent {
  scan_id: string;
  error: string;
  message: string;
  stage: string;
  retry_suggestions: string[];
  recoverable: boolean;
}

// From LLD Section 10.1 - API Response Types
export interface HealthCheckResponse {
  status: "ok" | "degraded";
  timestamp: string;
  services: Record<string, Record<string, any>>;
}

// From LLD Section 10.1 - Login Response
export interface LoginResponse {
  status: "success" | "new_user";
  user_exists: boolean;
  profile?: UserProfile;
  message?: string;
  redirect_to?: string;
}

// From LLD Section 10.1 - Profile Update Request
export interface ProfileUpdateRequest {
  demographics?: {
    age?: number;
    gender?: "male" | "female" | "other";
    height_cm?: number;
    weight_kg?: number;
  };
  lifestyle_habits?: {
    sleep_hours?: number;
    work_style?: "desk_job" | "light_activity" | "physical_job";
    exercise_frequency?: "rarely" | "1-2_times_week" | "3-4_times_week" | "5_times_week" | "daily";
    commute_type?: "car" | "public_transport" | "bike" | "walk";
    smoking?: "yes" | "no" | "occasionally";
    alcohol?: "none" | "light" | "moderate" | "heavy";
    stress_level?: "low" | "moderate" | "high";
  };
  goals?: {
    primary_goal?: "lose_weight" | "maintain_weight" | "gain_muscle";
    target_weight_kg?: number | null;
    timeline_weeks?: number | null;
  };
  food_preferences?: {
    cuisine_preferences?: string[];
    dietary_restrictions?: string[];
    allergens?: string[];
    disliked_ingredients?: string[];
  };
}

// From LLD Section 10.2 - Scan Request
export interface ScanRequest {
  user_name: string;
  image_base64: string;
  source: "camera" | "upload";
}