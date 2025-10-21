import React, { createContext, useContext } from "react";

type DashboardRefreshContextType = {
  refresh: () => void;
};

const DashboardRefreshContext = createContext<DashboardRefreshContextType>({
  refresh: () => {},
});

export const DashboardRefreshProvider = ({
  children,
  refresh,
}: {
  children: React.ReactNode;
  refresh: () => void;
}) => {
  return (
    <DashboardRefreshContext.Provider value={{ refresh }}>
      {children}
    </DashboardRefreshContext.Provider>
  );
};

export const useDashboardRefresh = () => {
  return useContext(DashboardRefreshContext);
};


