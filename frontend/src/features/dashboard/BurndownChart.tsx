import type { BurndownPoint } from "@/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const WIDTH = 560;
const HEIGHT = 200;
const PADDING = { top: 12, right: 12, bottom: 24, left: 36 };

/**
 * Lightweight, dependency-free actual-vs-ideal burndown (SCRUM-16 technical
 * design note: "keep light / dependency-minimal"). Actual vs Ideal are
 * distinguished by line style (solid vs dashed) *and* a text legend, not
 * colour alone (ux-spec §4.3 "burndown chart distinguishes Actual vs Ideal
 * by line style + label" -- WCAG 1.4.1). The exact series is also rendered
 * as a visually-hidden table so the same data is available as text (WCAG
 * 1.1.1 Non-text Content / 1.4.11 the SVG itself is decorative).
 */
export function BurndownChart({ burndown }: { burndown: BurndownPoint[] }) {
  if (burndown.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Story-point burndown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-text-secondary">No burndown data yet.</p>
        </CardContent>
      </Card>
    );
  }

  const maxValue = Math.max(
    ...burndown.map((p) => Math.max(p.ideal_remaining, p.actual_remaining)),
    1
  );
  const plotWidth = WIDTH - PADDING.left - PADDING.right;
  const plotHeight = HEIGHT - PADDING.top - PADDING.bottom;

  const xFor = (index: number) =>
    PADDING.left +
    (burndown.length === 1 ? 0 : (index / (burndown.length - 1)) * plotWidth);
  const yFor = (value: number) => PADDING.top + plotHeight * (1 - value / maxValue);

  const idealPath = burndown
    .map((p, i) => `${i === 0 ? "M" : "L"}${xFor(i)},${yFor(p.ideal_remaining)}`)
    .join(" ");
  const actualPath = burndown
    .map((p, i) => `${i === 0 ? "M" : "L"}${xFor(i)},${yFor(p.actual_remaining)}`)
    .join(" ");

  return (
    <Card>
      <CardHeader>
        <CardTitle>Story-point burndown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="mb-2 flex gap-4 text-xs font-medium text-text-secondary">
          <span className="flex items-center gap-1.5">
            <svg width="16" height="8" aria-hidden="true">
              <line x1="0" y1="4" x2="16" y2="4" stroke="var(--chart-actual)" strokeWidth="2" />
            </svg>
            Actual
          </span>
          <span className="flex items-center gap-1.5">
            <svg width="16" height="8" aria-hidden="true">
              <line
                x1="0"
                y1="4"
                x2="16"
                y2="4"
                stroke="var(--chart-ideal)"
                strokeWidth="2"
                strokeDasharray="3,3"
              />
            </svg>
            Ideal
          </span>
        </div>
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-labelledby="burndown-chart-title"
          className="w-full"
        >
          <title id="burndown-chart-title">
            Story points remaining, actual versus ideal, over the sprint
          </title>
          {/* baseline (>=3:1 non-text contrast, WCAG 1.4.11) */}
          <line
            x1={PADDING.left}
            y1={HEIGHT - PADDING.bottom}
            x2={WIDTH - PADDING.right}
            y2={HEIGHT - PADDING.bottom}
            stroke="var(--chart-baseline)"
            strokeWidth="1"
          />
          <path
            d={idealPath}
            fill="none"
            stroke="var(--chart-ideal)"
            strokeWidth="2"
            strokeDasharray="4,4"
          />
          <path d={actualPath} fill="none" stroke="var(--chart-actual)" strokeWidth="2.5" />
        </svg>

        <table className="sr-only">
          <caption>Burndown data by date: ideal versus actual points remaining</caption>
          <thead>
            <tr>
              <th scope="col">Date</th>
              <th scope="col">Ideal remaining</th>
              <th scope="col">Actual remaining</th>
            </tr>
          </thead>
          <tbody>
            {burndown.map((point) => (
              <tr key={point.date}>
                <th scope="row">{point.date}</th>
                <td>{point.ideal_remaining}</td>
                <td>{point.actual_remaining}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
