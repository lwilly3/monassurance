"use client";
import * as React from "react";
import { Slot } from "@radix-ui/react-slot";

type ButtonVariant = "primary" | "ghost" | "danger" | "outline";
type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const base =
  "inline-flex items-center justify-center gap-2 font-medium rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors";

const sizes: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-[var(--color-accent)] text-[var(--color-accent-contrast)] hover:brightness-110 focus-visible:ring-[var(--color-accent)]",
  ghost:
    "bg-transparent text-[var(--color-fg)] hover:bg-black/5 focus-visible:ring-[var(--color-accent)]",
  danger:
    "bg-[var(--color-danger)] text-[var(--color-danger-contrast)] hover:brightness-110 focus-visible:ring-[var(--color-danger)]",
  outline:
    "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus-visible:ring-[var(--color-accent)]",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ asChild, className = "", variant = "primary", size = "md", ...props }, ref) => {
  const Comp: React.ElementType = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={[base, sizes[size], variants[variant], className].join(" ")}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
