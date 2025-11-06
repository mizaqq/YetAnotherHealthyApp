import React, { createContext, useContext } from "react";
import { useAuthStore, clearPasswordRecovery as clearRecoveryFlag } from "@/lib/authStore";
import type { Session } from "@supabase/supabase-js";

type AuthContextType = {
  session: Session | null;
  loading: boolean;
  isPasswordRecovery: boolean;
  clearPasswordRecovery: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  // Use centralized auth store instead of local state
  const { status, session, isRecovery } = useAuthStore();
  
  // Derive loading state from status
  const loading = status === "loading";

  return (
    <AuthContext.Provider 
      value={{ 
        session, 
        loading, 
        isPasswordRecovery: isRecovery, 
        clearPasswordRecovery: clearRecoveryFlag 
      }}
    >
      {loading ? null : children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
};
