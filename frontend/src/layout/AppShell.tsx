import type { ReactNode } from "react";
import { LayoutDashboard } from "lucide-react";
import { SkipLink } from "@/components/SkipLink";

interface AppShellProps {
  /** Sticky top-bar content -- the project selector + connect entry point. */
  topBar: ReactNode;
  children: ReactNode;
}

/**
 * ux-spec §4.1: dark left nav (240px) with brand + primary sections +
 * persona/role footer; sticky top bar. MVP scope is a single dashboard
 * route (ARCHITECTURE.md §11 -- multi-project navigation is a project
 * *selector* in the top bar, not a router/portfolio view), so "primary
 * sections" is just the one entry, present for the "where am I" orientation
 * the nav is there to give (Nielsen #1).
 *
 * Focus order (ux-spec §4.4): skip-link -> nav -> top bar (project
 * selector -> connect CTA) -> page content.
 */
export function AppShell({ topBar, children }: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-canvas">
      <SkipLink />
      <nav
        aria-label="Primary"
        className="hidden w-60 shrink-0 flex-col justify-between bg-sidebar px-4 py-6 text-white md:flex"
      >
        <div>
          <div className="flex items-center gap-2 px-2 text-base font-semibold">
            <LayoutDashboard className="h-5 w-5" aria-hidden="true" />
            <span>Delivery Intelligence</span>
          </div>
          <ul className="mt-8 space-y-1">
            <li>
              <a
                href="#main-content"
                aria-current="page"
                className="block rounded-md bg-white/10 px-3 py-2 text-sm font-medium"
              >
                Dashboard
              </a>
            </li>
          </ul>
        </div>
        <div className="border-t border-white/10 px-2 pt-4 text-xs text-slate-300">
          Delivery Manager · Approver
        </div>
      </nav>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex flex-wrap items-center gap-3 border-b border-border bg-surface px-6 py-3">
          {topBar}
        </header>
        {children}
      </div>
    </div>
  );
}
