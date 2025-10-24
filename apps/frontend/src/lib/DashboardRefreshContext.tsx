import React, { createContext, useContext, useRef, useCallback } from "react";

type DashboardRefreshContextType = {
  refresh: () => void;
  registerRefresh: (callback: () => void) => void;
};

const DashboardRefreshContext = createContext<DashboardRefreshContextType>({
  refresh: () => {},
  registerRefresh: () => {},
});

export const DashboardRefreshProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const refreshCallbackRef = useRef<(() => void) | null>(null);

  const registerRefresh = useCallback((callback: () => void) => {
    refreshCallbackRef.current = callback;
  }, []);

  const refresh = useCallback(() => {
    refreshCallbackRef.current?.();
  }, []);

  return (
    <DashboardRefreshContext.Provider value={{ refresh, registerRefresh }}>
      {children}
    </DashboardRefreshContext.Provider>
  );
};

export const useDashboardRefresh = () => {
  return useContext(DashboardRefreshContext);
};


