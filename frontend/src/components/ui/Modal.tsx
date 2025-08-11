"use client";
import * as React from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { Button } from "./Button";

export interface ModalProps {
  title: string;
  description?: string;
  trigger?: React.ReactNode;
  children: React.ReactNode;
}

export function Modal({ title, description, trigger, children }: ModalProps) {
  return (
    <Dialog.Root>
      {trigger && <Dialog.Trigger asChild>{trigger}</Dialog.Trigger>}
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 data-[state=open]:animate-fade-in" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 w-[90vw] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-lg bg-[var(--color-bg)] p-6 shadow-lg focus:outline-none data-[state=open]:animate-pop-in"
          aria-describedby={description ? undefined : ""}
       >
          <Dialog.Title className="text-lg font-semibold text-[var(--color-fg)]">
            {title}
          </Dialog.Title>
          {description && (
            <Dialog.Description className="mt-1 text-sm text-[var(--color-muted)]">
              {description}
            </Dialog.Description>
          )}
          <div className="mt-4">{children}</div>
          <div className="mt-6 flex justify-end gap-2">
            <Dialog.Close asChild>
              <Button variant="ghost">Fermer</Button>
            </Dialog.Close>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
