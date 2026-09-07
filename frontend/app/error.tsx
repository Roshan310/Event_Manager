"use client";
import { ErrorState } from "@/components/feedback";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <ErrorState
      error={new Error("This page couldn’t load. Please try again.")}
      retry={reset}
    />
  );
}
