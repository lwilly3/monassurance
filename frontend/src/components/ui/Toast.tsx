"use client";
import * as React from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";
import { Button } from "./Button";

export interface ToastProps {
  title: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  open?: boolean;
  onOpenChange?: (v: boolean) => void;
}

export function Toast({ title, description, actionText, onAction, open, onOpenChange }: ToastProps) {
  return (
    <ToastPrimitive.Provider swipeDirection="right">
      <ToastPrimitive.Root
        className="rounded-md bg-[var(--color-primary)] text-[var(--color-primary-contrast)] shadow-lg data-[state=open]:animate-slide-in data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)] data-[swipe=cancel]:translate-x-0 data-[swipe=end]:animate-slide-out"
        open={open}
        onOpenChange={onOpenChange}
      >
        <div className="px-4 py-3">
          <ToastPrimitive.Title className="font-semibold">{title}</ToastPrimitive.Title>
          {description && (
            <ToastPrimitive.Description className="text-sm opacity-90">
              {description}
            </ToastPrimitive.Description>
          )}
          {actionText && (
            <ToastPrimitive.Action altText={actionText} asChild>
              <Button variant="ghost" className="mt-2 border border-white/20">
                {actionText}
              </Button>
            </ToastPrimitive.Action>
          )}
        </div>
        <ToastPrimitive.Close className="absolute right-2 top-2 text-white/80 hover:text-white" aria-label="Fermer">
          ×
        </ToastPrimitive.Close>
      </ToastPrimitive.Root>
      <ToastPrimitive.Viewport className="fixed bottom-2 right-2 z-50 flex w-96 flex-col gap-2 outline-none" />
    </ToastPrimitive.Provider>
  );
}
