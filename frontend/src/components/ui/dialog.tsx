import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

// shadcn/ui-style Dialog wrapper over @radix-ui/react-dialog (hand-added,
// see button.tsx comment on the CLI). Radix supplies the accessibility
// contract the ux-spec requires for the explanation drawer (§5.3 High
// finding): focus moves into the dialog on open, Tab is trapped inside it,
// Esc closes it, and focus returns to the trigger on close -- all native
// Radix Dialog behavior, not reimplemented here.
export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;

export function DialogContent({
  className,
  children,
  title,
  ...props
}: React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> & { title: string }) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-slate-900/40 data-[state=open]:animate-fade-in" />
      <DialogPrimitive.Content
        className={cn(
          "fixed inset-y-0 right-0 z-50 flex w-full max-w-[760px] flex-col overflow-y-auto bg-surface shadow-xl focus:outline-none",
          className
        )}
        {...props}
      >
        <div className="flex items-start justify-between gap-4 bg-sidebar px-6 py-5 text-white">
          <DialogPrimitive.Title className="text-lg font-bold">{title}</DialogPrimitive.Title>
          <DialogPrimitive.Close asChild>
            <button
              type="button"
              aria-label="Close"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md hover:bg-white/10"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </DialogPrimitive.Close>
        </div>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

export const DialogDescription = DialogPrimitive.Description;
