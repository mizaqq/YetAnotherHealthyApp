import type {
  Tables,
  TablesInsert,
  TablesUpdate,
  Enums,
} from "./db/database.types";

// Common helpers
export type ISODateTimeString = string;
export type ISODateString = string;

// Pagination envelope used by many list endpoints
export type PageMeta = {
  size: number;
  after?: string | null;
};

export type PaginatedResponse<TItem> = {
  data: TItem[];
  page: PageMeta;
};

// Enumerations surfaced by the API (sourced from DB enums)
export type MealSource = Enums<"meal_source">;
export type AnalysisRunStatus = Enums<"analysis_run_status">;

// Reusable macros representations
export type ProductMacrosPer100g = {
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
};

// 2.2 Profile
export type ProfileDTO = Pick<
  Tables<"profiles">,
  "user_id" | "daily_calorie_goal" | "onboarding_completed_at" | "created_at" | "updated_at"
>;

export type CreateOnboardingCommand = Pick<
  TablesInsert<"profiles">,
  "daily_calorie_goal"
>;

export type UpdateProfileCommand = Pick<
  TablesUpdate<"profiles">,
  "daily_calorie_goal" | "onboarding_completed_at"
>;

// 2.3 Meal Categories
export type MealCategoryDTO = Omit<
  Tables<"meal_categories">,
  "created_at"
>;

// 2.4 Units
export type UnitDefinitionDTO = Pick<
  Tables<"unit_definitions">,
  "id" | "code" | "unit_type" | "grams_per_unit"
>;

export type UnitAliasDTO = Pick<
  Tables<"unit_aliases">,
  "alias" | "locale" | "is_primary"
>;

export type UnitAliasesDTO = {
  unit_id: Tables<"unit_definitions">["id"];
  aliases: UnitAliasDTO[];
};

// 2.5 Products
export type ProductListItemDTO = Pick<
  Tables<"products">,
  "id" | "name" | "source"
> & {
  // Strongly-typed view of the JSON column from DB
  macros_per_100g: ProductMacrosPer100g;
};

export type ProductPortionDTO = Pick<
  Tables<"product_portions">,
  "id" | "unit_definition_id" | "grams_per_portion" | "is_default" | "source"
>;

export type ProductDetailDTO = Pick<
  Tables<"products">,
  "id" | "name" | "off_id" | "source" | "created_at" | "updated_at"
> & {
  macros_per_100g: ProductMacrosPer100g;
  portions?: ProductPortionDTO[];
};

// 2.6 Meals
type MealRow = Tables<"meals">;
type MealInsert = TablesInsert<"meals">;
type MealUpdate = TablesUpdate<"meals">;
type AnalysisRunRow = Tables<"analysis_runs">;

export type CreateMealCommand = Pick<
  MealInsert,
  "category" | "eaten_at" | "source" | "calories" | "protein" | "fat" | "carbs"
> & {
  // Not stored directly on meals, but required for AI/edited sources per API rules
  analysis_run_id?: AnalysisRunRow["id"];
  // Optional client-provided note (not persisted in current DB schema)
  notes?: string;
};

export type MealListItemDTO = Pick<
  MealRow,
  | "id"
  | "category"
  | "eaten_at"
  | "calories"
  | "protein"
  | "fat"
  | "carbs"
  | "source"
  | "accepted_analysis_run_id"
>;

export type MealAnalysisRunSummaryDTO = Pick<
  AnalysisRunRow,
  "id" | "status" | "run_no"
>;

export type MealAnalysisItemDTO = Pick<
  Tables<"analysis_run_items">,
  | "id"
  | "ordinal"
  | "raw_name"
  | "weight_grams"
  | "calories"
  | "protein"
  | "fat"
  | "carbs"
  | "confidence"
>;

export type MealDetailDTO = Pick<
  MealRow,
  "id" | "category" | "eaten_at" | "source" | "calories" | "protein" | "fat" | "carbs"
> & {
  analysis?: {
    run: MealAnalysisRunSummaryDTO;
    items?: MealAnalysisItemDTO[];
  };
};

export type UpdateMealCommand = Partial<
  Pick<
    MealUpdate,
    "category" | "eaten_at" | "calories" | "protein" | "fat" | "carbs" | "source"
  >
> & {
  analysis_run_id?: AnalysisRunRow["id"];
};

// 2.7 Analysis Runs
export type CreateAnalysisRunCommand = {
  meal_id?: Tables<"meals">["id"] | null;
  input_text: string;
  threshold?: number; // bounded 0..1 per API rules
};

export type AnalysisRunListItemDTO = Pick<
  AnalysisRunRow,
  "id" | "meal_id" | "run_no" | "status" | "threshold_used" | "created_at" | "completed_at"
>;

export type AnalysisRunDetailDTO = Pick<
  AnalysisRunRow,
  |
    "id"
  | "meal_id"
  | "run_no"
  | "status"
  | "latency_ms"
  | "tokens"
  | "cost_minor_units"
  | "cost_currency"
  | "threshold_used"
  | "retry_of_run_id"
  | "error_code"
  | "error_message"
  | "created_at"
  | "completed_at"
>;

export type AnalysisRunItemDTO = Pick<
  Tables<"analysis_run_items">,
  |
    "id"
  | "ordinal"
  | "raw_name"
  | "raw_unit"
  | "quantity"
  | "unit_definition_id"
  | "product_id"
  | "product_portion_id"
  | "weight_grams"
  | "confidence"
  | "calories"
  | "protein"
  | "fat"
  | "carbs"
>;

export type AnalysisRunItemsDTO = {
  run_id: AnalysisRunRow["id"];
  items: AnalysisRunItemDTO[];
};

export type RetryAnalysisRunCommand = {
  threshold?: number;
  raw_input?: {
    text?: string;
    overrides?: {
      excluded_ingredients?: string[];
      notes?: string;
    };
  };
};

export type CancelAnalysisRunCommand = undefined;

// 2.8 Reports
export type DailySummaryReportDTO = {
  date: ISODateString;
  calorie_goal: Tables<"profiles">["daily_calorie_goal"];
  totals: {
    calories: number;
    protein: number;
    fat: number;
    carbs: number;
  };
  progress: {
    calories_percentage: number;
  };
  meals: Array<
    Pick<
      MealRow,
      "id" | "category" | "calories" | "eaten_at" | "protein" | "fat" | "carbs"
    >
  >;
};

export type WeeklyTrendReportPointDTO = {
  date: ISODateString;
  calories: number;
  goal: number;
};

export type WeeklyTrendReportDTO = {
  start_date: ISODateString;
  end_date: ISODateString;
  points: WeeklyTrendReportPointDTO[];
};

export type Meal = Pick<
  Tables<"meals">,
  "id" | "category" | "calories" | "protein" | "fat" | "carbs"
>;

export type AuthMode = "login" | "register";

export interface AuthFormData {
  email: string;
  password: string;
}

export interface AuthFormProps {
  mode: AuthMode;
  onSubmit: (data: AuthFormData) => void;
  isLoading: boolean;
  apiError: string | null;
}

// Add Meal Modal ViewModels
export type MealInputFormViewModel = {
  category: string;
  description: string;
  isManualMode: boolean;
  manualCalories: number | null;
};

export type AnalysisResultsViewModel = {
  runId: string;
  totals: {
    calories: number;
    protein: number;
    fat: number;
    carbs: number;
  };
  items: AnalysisRunItemDTO[];
};

// Onboarding ViewModels
export type OnboardingFormProps = {
  onSubmit: (data: CreateOnboardingCommand) => void;
  isLoading: boolean;
  apiError: string | null;
};
