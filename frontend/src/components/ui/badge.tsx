import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "blue" | "purple" | "green" | "gray" | "destructive";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
        variant === "default" &&
          "border-transparent bg-slate-900 text-white hover:bg-slate-800",
        variant === "secondary" &&
          "border-transparent bg-slate-100 text-slate-900 hover:bg-slate-200",
        variant === "outline" &&
          "border-slate-200 text-slate-950",
        variant === "blue" &&
          "border-transparent bg-blue-100 text-blue-700",
        variant === "purple" &&
          "border-transparent bg-violet-100 text-violet-700",
        variant === "green" &&
          "border-transparent bg-emerald-100 text-emerald-700",
        variant === "destructive" &&
          "border-transparent bg-red-100 text-red-700",
        variant === "gray" &&
          "border-transparent bg-slate-100 text-slate-600",
        className
      )}
      {...props}
    />
  );
}

export { Badge };
