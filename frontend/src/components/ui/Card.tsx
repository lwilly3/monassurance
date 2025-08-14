import * as React from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function Card({ className = "", children, ...props }: CardProps) {
  return (
    <div
      className={[
        "rounded-lg border border-gray-200 bg-white shadow-sm",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function CardHeader({ className = "", children, ...props }: CardHeaderProps) {
  return (
    <div
      className={[
        "flex flex-col space-y-1.5 p-6",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
}

export function CardTitle({ className = "", children, ...props }: CardTitleProps) {
  return (
    <h3
      className={[
        "text-lg font-semibold leading-none tracking-tight",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </h3>
  );
}

export interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
}

export function CardDescription({ className = "", children, ...props }: CardDescriptionProps) {
  return (
    <p
      className={[
        "text-sm text-gray-500",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </p>
  );
}

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function CardContent({ className = "", children, ...props }: CardContentProps) {
  return (
    <div
      className={[
        "p-6 pt-0",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export function CardFooter({ className = "", children, ...props }: CardFooterProps) {
  return (
    <div
      className={[
        "flex items-center p-6 pt-0",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
