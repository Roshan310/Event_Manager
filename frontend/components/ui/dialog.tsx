"use client";
import { Dialog as Primitive } from "radix-ui";
import { X } from "lucide-react";
import type { ComponentProps } from "react";
export const Dialog = Primitive.Root;
export const DialogTrigger = Primitive.Trigger;
export const DialogTitle = Primitive.Title;
export const DialogDescription = Primitive.Description;
export function DialogContent({
  children,
  ...props
}: ComponentProps<typeof Primitive.Content>) {
  return (
    <Primitive.Portal>
      <Primitive.Overlay className="dialog-overlay" />
      <Primitive.Content className="dialog-content" {...props}>
        {children}
        <Primitive.Close className="dialog-close" aria-label="Close dialog">
          <X size={18} />
        </Primitive.Close>
      </Primitive.Content>
    </Primitive.Portal>
  );
}
