import * as React from "react";

export interface LoaderProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "md" | "lg";
}

export function Loader({ className = "", size = "md", ...props }: LoaderProps) {
  const sizeStyles = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  };

  return (
    <div
      className={[
        "animate-spin rounded-full border-2 border-gray-300 border-t-blue-600",
        sizeStyles[size],
        className,
      ].join(" ")}
      {...props}
    />
  );
}

export interface LoadingSpinnerProps {
  text?: string;
  size?: "sm" | "md" | "lg";
}

export function LoadingSpinner({ text = "Chargement...", size = "md" }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center space-y-2 p-4">
      <Loader size={size} />
      <p className="text-sm text-gray-500">{text}</p>
    </div>
  );
}

export interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  text?: string;
}

export function LoadingOverlay({ isLoading, children, text = "Chargement..." }: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
          <LoadingSpinner text={text} />
        </div>
      )}
    </div>
  );
}
