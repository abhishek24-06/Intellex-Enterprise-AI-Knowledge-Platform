"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import { initials } from "@/lib/utils";

function Avatar({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex size-8 shrink-0 select-none items-center justify-center overflow-hidden rounded-full bg-indigo-100 text-xs font-semibold text-indigo-700",
        className,
      )}
    >
      {initials(name) || "?"}
    </span>
  );
}

export { Avatar };
