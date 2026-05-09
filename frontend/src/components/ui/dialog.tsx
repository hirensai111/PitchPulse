import * as React from "react";
import { cn } from "@/lib/utils";

const DialogContext = React.createContext<{
  open: boolean;
  setOpen: (v: boolean) => void;
} | null>(null);

function Dialog({
  children,
  open,
  onOpenChange,
}: {
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (v: boolean) => void;
}) {
  const [internalOpen, setInternalOpen] = React.useState(false);
  const isOpen = open !== undefined ? open : internalOpen;
  const setIsOpen = onOpenChange || setInternalOpen;

  return (
    <DialogContext.Provider value={{ open: isOpen, setOpen: setIsOpen }}>
      {children}
    </DialogContext.Provider>
  );
}

function DialogTrigger({ children }: { children: React.ReactNode }) {
  const ctx = React.useContext(DialogContext);
  if (!ctx) return null;

  const handleClick = () => ctx.setOpen(true);

  return (
    <button onClick={handleClick} className="inline-flex">
      {children}
    </button>
  );
}

function DialogContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const ctx = React.useContext(DialogContext);
  if (!ctx || !ctx.open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/40"
        onClick={() => ctx.setOpen(false)}
      />
      <div
        className={cn(
          "relative z-50 bg-white rounded-lg border border-slate-200 shadow-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto",
          className
        )}
      >
        {children}
      </div>
    </div>
  );
}

function DialogHeader({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col space-y-1.5 mb-4", className)}>
      {children}
    </div>
  );
}

function DialogTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h2
      className={cn(
        "text-lg font-semibold leading-none tracking-tight text-slate-900",
        className
      )}
    >
      {children}
    </h2>
  );
}

export { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle };
