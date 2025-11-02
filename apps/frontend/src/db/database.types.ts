/* eslint-disable @typescript-eslint/consistent-indexed-object-style, @typescript-eslint/no-redundant-type-constituents */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  __InternalSupabase: {
    PostgrestVersion: string;
  };
  graphql_public: {
    Tables: {
      [_ in never]: never
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      graphql: {
        Args: {
          extensions?: Json
          operationName?: string
          query?: string
          variables?: Json
        }
        Returns: Json
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
  public: {
    Tables: {
      analysis_run_items: {
        Row: {
          calories: number | null
          carbs: number | null
          confidence: number | null
          created_at: string
          fat: number | null
          id: string
          ordinal: number
          product_id: string | null
          product_portion_id: string | null
          protein: number | null
          quantity: number
          raw_name: string
          raw_unit: string | null
          run_id: string
          unit_definition_id: string | null
          user_id: string
          weight_grams: number | null
        }
        Insert: {
          calories?: number | null
          carbs?: number | null
          confidence?: number | null
          created_at?: string
          fat?: number | null
          id?: string
          ordinal: number
          product_id?: string | null
          product_portion_id?: string | null
          protein?: number | null
          quantity: number
          raw_name: string
          raw_unit?: string | null
          run_id: string
          unit_definition_id?: string | null
          user_id: string
          weight_grams?: number | null
        }
        Update: {
          calories?: number | null
          carbs?: number | null
          confidence?: number | null
          created_at?: string
          fat?: number | null
          id?: string
          ordinal?: number
          product_id?: string | null
          product_portion_id?: string | null
          protein?: number | null
          quantity?: number
          raw_name?: string
          raw_unit?: string | null
          run_id?: string
          unit_definition_id?: string | null
          user_id?: string
          weight_grams?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "analysis_run_items_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "analysis_run_items_product_portion_id_fkey"
            columns: ["product_portion_id"]
            isOneToOne: false
            referencedRelation: "product_portions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "analysis_run_items_run_id_fkey"
            columns: ["run_id"]
            isOneToOne: false
            referencedRelation: "analysis_runs"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "analysis_run_items_run_user_fk"
            columns: ["run_id", "user_id"]
            isOneToOne: false
            referencedRelation: "analysis_runs"
            referencedColumns: ["id", "user_id"]
          },
          {
            foreignKeyName: "analysis_run_items_unit_definition_id_fkey"
            columns: ["unit_definition_id"]
            isOneToOne: false
            referencedRelation: "unit_definitions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "analysis_run_items_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["user_id"]
          },
        ]
      }
      analysis_runs: {
        Row: {
          completed_at: string | null
          cost_currency: string
          cost_minor_units: number | null
          created_at: string
          error_code: string | null
          error_message: string | null
          id: string
          latency_ms: number | null
          meal_id: string
          model: string
          raw_input: Json
          raw_output: Json | null
          retry_of_run_id: string | null
          run_no: number
          status: Database["public"]["Enums"]["analysis_run_status"]
          threshold_used: number | null
          tokens: number | null
          user_id: string
        }
        Insert: {
          completed_at?: string | null
          cost_currency?: string
          cost_minor_units?: number | null
          created_at?: string
          error_code?: string | null
          error_message?: string | null
          id?: string
          latency_ms?: number | null
          meal_id: string
          model: string
          raw_input: Json
          raw_output?: Json | null
          retry_of_run_id?: string | null
          run_no: number
          status: Database["public"]["Enums"]["analysis_run_status"]
          threshold_used?: number | null
          tokens?: number | null
          user_id: string
        }
        Update: {
          completed_at?: string | null
          cost_currency?: string
          cost_minor_units?: number | null
          created_at?: string
          error_code?: string | null
          error_message?: string | null
          id?: string
          latency_ms?: number | null
          meal_id?: string
          model?: string
          raw_input?: Json
          raw_output?: Json | null
          retry_of_run_id?: string | null
          run_no?: number
          status?: Database["public"]["Enums"]["analysis_run_status"]
          threshold_used?: number | null
          tokens?: number | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "analysis_runs_meal_id_fkey"
            columns: ["meal_id"]
            isOneToOne: false
            referencedRelation: "meals"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "analysis_runs_meal_user_fk"
            columns: ["meal_id", "user_id"]
            isOneToOne: false
            referencedRelation: "meals"
            referencedColumns: ["id", "user_id"]
          },
          {
            foreignKeyName: "analysis_runs_retry_user_fk"
            columns: ["retry_of_run_id", "user_id"]
            isOneToOne: false
            referencedRelation: "analysis_runs"
            referencedColumns: ["id", "user_id"]
          },
          {
            foreignKeyName: "analysis_runs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["user_id"]
          },
        ]
      }
      meal_categories: {
        Row: {
          code: string
          created_at: string
          label: string
          sort_order: number
        }
        Insert: {
          code: string
          created_at?: string
          label: string
          sort_order: number
        }
        Update: {
          code?: string
          created_at?: string
          label?: string
          sort_order?: number
        }
        Relationships: []
      }
      meals: {
        Row: {
          accepted_analysis_run_id: string | null
          calories: number
          carbs: number | null
          category: string
          created_at: string
          deleted_at: string | null
          eaten_at: string
          fat: number | null
          id: string
          protein: number | null
          source: Database["public"]["Enums"]["meal_source"]
          updated_at: string
          user_id: string
        }
        Insert: {
          accepted_analysis_run_id?: string | null
          calories: number
          carbs?: number | null
          category: string
          created_at?: string
          deleted_at?: string | null
          eaten_at: string
          fat?: number | null
          id?: string
          protein?: number | null
          source?: Database["public"]["Enums"]["meal_source"]
          updated_at?: string
          user_id: string
        }
        Update: {
          accepted_analysis_run_id?: string | null
          calories?: number
          carbs?: number | null
          category?: string
          created_at?: string
          deleted_at?: string | null
          eaten_at?: string
          fat?: number | null
          id?: string
          protein?: number | null
          source?: Database["public"]["Enums"]["meal_source"]
          updated_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "meals_accepted_analysis_run_fk"
            columns: ["accepted_analysis_run_id"]
            isOneToOne: false
            referencedRelation: "analysis_runs"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "meals_category_fkey"
            columns: ["category"]
            isOneToOne: false
            referencedRelation: "meal_categories"
            referencedColumns: ["code"]
          },
          {
            foreignKeyName: "meals_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "profiles"
            referencedColumns: ["user_id"]
          },
        ]
      }
      product_portions: {
        Row: {
          created_at: string
          grams_per_portion: number
          id: string
          is_default: boolean
          product_id: string
          source: string | null
          unit_definition_id: string
        }
        Insert: {
          created_at?: string
          grams_per_portion: number
          id?: string
          is_default?: boolean
          product_id: string
          source?: string | null
          unit_definition_id: string
        }
        Update: {
          created_at?: string
          grams_per_portion?: number
          id?: string
          is_default?: boolean
          product_id?: string
          source?: string | null
          unit_definition_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "product_portions_product_id_fkey"
            columns: ["product_id"]
            isOneToOne: false
            referencedRelation: "products"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "product_portions_unit_definition_id_fkey"
            columns: ["unit_definition_id"]
            isOneToOne: false
            referencedRelation: "unit_definitions"
            referencedColumns: ["id"]
          },
        ]
      }
      products: {
        Row: {
          created_at: string
          id: string
          macros_per_100g: Json
          name: string
          off_id: string | null
          source: string
          updated_at: string
        }
        Insert: {
          created_at?: string
          id?: string
          macros_per_100g: Json
          name: string
          off_id?: string | null
          source: string
          updated_at?: string
        }
        Update: {
          created_at?: string
          id?: string
          macros_per_100g?: Json
          name?: string
          off_id?: string | null
          source?: string
          updated_at?: string
        }
        Relationships: []
      }
      profiles: {
        Row: {
          created_at: string
          daily_calorie_goal: number
          onboarding_completed_at: string | null
          timezone: string
          updated_at: string
          user_id: string
        }
        Insert: {
          created_at?: string
          daily_calorie_goal: number
          onboarding_completed_at?: string | null
          timezone?: string
          updated_at?: string
          user_id: string
        }
        Update: {
          created_at?: string
          daily_calorie_goal?: number
          onboarding_completed_at?: string | null
          timezone?: string
          updated_at?: string
          user_id?: string
        }
        Relationships: []
      }
      unit_aliases: {
        Row: {
          alias: string
          created_at: string
          is_primary: boolean
          locale: string
          unit_definition_id: string
        }
        Insert: {
          alias: string
          created_at?: string
          is_primary?: boolean
          locale?: string
          unit_definition_id: string
        }
        Update: {
          alias?: string
          created_at?: string
          is_primary?: boolean
          locale?: string
          unit_definition_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "unit_aliases_unit_definition_id_fkey"
            columns: ["unit_definition_id"]
            isOneToOne: false
            referencedRelation: "unit_definitions"
            referencedColumns: ["id"]
          },
        ]
      }
      unit_definitions: {
        Row: {
          code: string
          created_at: string
          grams_per_unit: number
          id: string
          unit_type: string
          updated_at: string
        }
        Insert: {
          code: string
          created_at?: string
          grams_per_unit: number
          id?: string
          unit_type: string
          updated_at?: string
        }
        Update: {
          code?: string
          created_at?: string
          grams_per_unit?: number
          id?: string
          unit_type?: string
          updated_at?: string
        }
        Relationships: []
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      analysis_run_status:
        | "queued"
        | "running"
        | "succeeded"
        | "failed"
        | "cancelled"
      meal_source: "ai" | "edited" | "manual"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  graphql_public: {
    Enums: {},
  },
  public: {
    Enums: {
      analysis_run_status: [
        "queued",
        "running",
        "succeeded",
        "failed",
        "cancelled",
      ],
      meal_source: ["ai", "edited", "manual"],
    },
  },
} as const

