import * as React from "react";
import { AlertTriangle, Inbox, Loader2, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed bg-card px-6 py-14 text-center",
        className,
      )}
    >
      <span className="mb-3 flex size-10 items-center justify-center rounded-full bg-muted">
        <Icon className="size-5 text-muted-foreground" />
      </span>
      <p className="text-sm font-medium">{title}</p>
      {description ? (
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-red-200 bg-red-50/60 px-6 py-12 text-center",
        className,
      )}
    >
      <span className="mb-3 flex size-10 items-center justify-center rounded-full bg-red-100">
        <AlertTriangle className="size-5 text-destructive" />
      </span>
      <p className="text-sm font-medium text-red-900">{title}</p>
      {message ? <p className="mt-1 max-w-md text-sm text-red-700/90">{message}</p> : null}
      {onRetry ? (
        <Button variant="outline" size="sm" className="mt-4" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

export function PermissionDeniedState({ message }: { message?: string }) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center rounded-lg border border-amber-200 bg-amber-50 px-6 py-14 text-center"
    >
      <span className="mb-3 flex size-10 items-center justify-center rounded-full bg-amber-100">
        <ShieldAlert className="size-5 text-warning" />
      </span>
      <p className="text-sm font-semibold text-amber-900">Permission denied</p>
      <p className="mt-1 max-w-md text-sm text-amber-800/90">
        {message ??
          "Your account is not authorized to perform this action. Contact your organization administrator if you believe this is a mistake."}
      </p>
    </div>
  );
}

export function LoadingBlock({
  label = "Loading…",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div
      className={cn("flex flex-col items-center justify-center gap-3 py-16", className)}
      aria-busy
      aria-live="polite"
    >
      <Loader2 className="size-6 animate-spin text-muted-foreground" />
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}
