import { AppShell } from "./layout/AppShell";
import { DashboardPage } from "./features/dashboard/DashboardPage";

// MVP scope is a single project/sprint dashboard route (ARCHITECTURE.md §11
// -- project switcher / multi-project is explicitly roadmap). No router is
// introduced for one screen.
export default function App() {
  return (
    <AppShell>
      <DashboardPage />
    </AppShell>
  );
}
