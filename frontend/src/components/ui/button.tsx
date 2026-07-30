import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// shadcn/ui-style primitive (hand-added: this environment's Node version is
// too old for the `shadcn` CLI's ESM build -- see frontend/README.md
// "Design system" note). Structure/variants follow the standard shadcn
// `button` component so it stays a drop-in swap once the CLI can run here.
const buttonVariants = cva(
  // min 24x24 target size (WCAG 2.5.8) via padding; visible focus ring via
  // global :focus-visible in index.css.
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 min-h-[36px]",
  {
    variants: {
      variant: {
        default: "bg-sidebar text-white hover:bg-slate-800",
        destructive: "bg-status-red text-white hover:bg-red-800",
        outline:
          "border border-slate-300 bg-surface text-text-primary hover:bg-subtle",
        ghost: "text-text-primary hover:bg-subtle",
        link: "text-status-info underline-offset-4 hover:underline p-0 min-h-0",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-6",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
