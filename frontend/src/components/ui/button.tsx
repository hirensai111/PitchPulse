import * as React from "react";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
          variant === "default" &&
            "bg-slate-900 text-white hover:bg-slate-800",
          variant === "outline" &&
            "border border-slate-200 bg-transparent hover:bg-slate-100 text-slate-900",
          variant === "ghost" &&
            "hover:bg-slate-100 text-slate-900",
          variant === "secondary" &&
            "bg-slate-100 text-slate-900 hover:bg-slate-200",
          size === "default" && "h-10 px-4 py-2 text-sm",
          size === "sm" && "h-8 px-3 text-xs",
          size === "lg" && "h-11 px-8 text-base",
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
