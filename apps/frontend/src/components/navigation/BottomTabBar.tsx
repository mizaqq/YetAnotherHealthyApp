import { useLocation, useNavigate } from "react-router-dom";
import {
  TabList,
  Tab,
  makeStyles,
  shorthands,
  tokens,
} from "@fluentui/react-components";
import {
  HomeRegular,
  HomeFilled,
  HistoryRegular,
  HistoryFilled,
  PersonRegular,
  PersonFilled,
} from "@fluentui/react-icons";

const useStyles = makeStyles({
  root: {
    position: "fixed",
    bottom: 0,
    left: 0,
    right: 0,
    zIndex: 40,
    backgroundColor: tokens.colorNeutralBackground1,
    borderTopWidth: "1px",
    borderTopStyle: "solid",
    borderTopColor: tokens.colorNeutralStroke2,
    paddingBottom: "env(safe-area-inset-bottom)",
    boxShadow: tokens.shadow8,
  },
  tabList: {
    justifyContent: "space-around",
    height: "64px",
    width: "100%",
  },
  tab: {
    flex: "1 1 0",
    minWidth: "80px",
    maxWidth: "none",
    height: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding("6px", "8px"),
    ...shorthands.gap("2px"),
    ...shorthands.overflow("visible"),
    fontSize: tokens.fontSizeBase200,
    lineHeight: tokens.lineHeightBase200,
  },
});

type TabConfig = {
  path: string;
  label: string;
  icon: React.ReactElement;
  activeIcon: React.ReactElement;
};

const tabs: TabConfig[] = [
  {
    path: "/",
    label: "Dzisiaj",
    icon: <HomeRegular />,
    activeIcon: <HomeFilled />,
  },
  {
    path: "/history",
    label: "Historia",
    icon: <HistoryRegular />,
    activeIcon: <HistoryFilled />,
  },
  {
    path: "/profile",
    label: "Profil",
    icon: <PersonRegular />,
    activeIcon: <PersonFilled />,
  },
];

export function BottomTabBar(): JSX.Element {
  const styles = useStyles();
  const location = useLocation();
  const navigate = useNavigate();

  const getActiveTab = (): string => {
    const currentPath = location.pathname;
    const matchingTab = tabs.find((tab) => tab.path === currentPath);
    return matchingTab?.path || "/";
  };

  const handleTabSelect = (_event: unknown, data: { value: string }) => {
    navigate(data.value);
  };

  const activeTab = getActiveTab();

  return (
    <nav className={styles.root} role="navigation" aria-label="Główna nawigacja">
      <TabList
        selectedValue={activeTab}
        onTabSelect={handleTabSelect}
        className={styles.tabList}
        appearance="transparent"
        size="medium"
        vertical={false}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.path;
          return (
            <Tab
              key={tab.path}
              value={tab.path}
              icon={isActive ? tab.activeIcon : tab.icon}
              aria-label={tab.label}
              aria-current={isActive ? "page" : undefined}
              className={styles.tab}
            >
              {tab.label}
            </Tab>
          );
        })}
      </TabList>
    </nav>
  );
}

