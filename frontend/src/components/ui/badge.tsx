import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Status is ALWAYS paired with a text label + icon by the caller (WCAG
// 1.4.1 Use of Color / ux-spec §3) -- this component supplies the color
// pairing, never color alone.
const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
  {
    variants: {
      variant: {
        green: "bg-status-green-bg text-status-green border-status-green-border",
        red: "bg-status-red-bg text-status-red border-status-red-border",
        amber: "bg-status-amber-bg text-status-amber border-status-amber-border",
        info: "bg-status-info-bg text-status-info border-status-info-border",
        neutral: "bg-subtle text-text-secondary border-slate-200",
      },
    },
    defaultVariants: { variant: "neutral" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
