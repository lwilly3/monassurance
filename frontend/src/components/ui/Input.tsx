import * as React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ id, label, error, hint, className = "", ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const hintId = hint ? `${inputId}-hint` : undefined;
    const errorId = error ? `${inputId}-error` : undefined;
    const describedBy = [hintId, errorId].filter(Boolean).join(" ");

    return (
      <div className="flex flex-col gap-1">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-[var(--color-fg)]">
            {label}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          aria-invalid={!!error}
          aria-describedby={describedBy || undefined}
          className={[
            "h-10 rounded-md border border-black/10 bg-white px-3 text-sm text-[var(--color-fg)]",
            "placeholder:text-[var(--color-muted)]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-[var(--color-accent)]",
            error ? "border-[var(--color-danger)]" : "",
            className,
          ].join(" ")}
          {...props}
        />
        {hint && (
          <div id={hintId} className="text-xs text-[var(--color-muted)]">
            {hint}
          </div>
        )}
        {error && (
          <div id={errorId} className="text-xs text-[var(--color-danger)]">
            {error}
          </div>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";
