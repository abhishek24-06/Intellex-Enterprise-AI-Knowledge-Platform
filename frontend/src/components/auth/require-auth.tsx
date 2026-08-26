"use client";

import { useRouter, usePathname } from "next/navigation";
import * as React from "react";
import Link from "next/link";
import { ShieldAlert } from "lucide-react";

import { useAuth } from "@/providers/auth-provider";
import type { UserRole } from "@/types/api";

function FullPageSpinner({ label }: { label: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3" aria-busy>
      <span className="size-6 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}

/**
 * Client-side route guard.
 *
 * This exists purely for UX/navigation. The FastAPI backend remains the real
 * security boundary for every request.
 */
export function RequireAuth({
  roles,
  children,
}: {
  roles?: UserRole[];
  children: React.ReactNode;
}) {
  const { status, user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const authorized =
    user !== null && (roles === undefined || roles.includes(user.role));

  React.useEffect(() => {
    if (status === "unauthenticated") {
      const next = pathname ? `?next=${encodeURIComponent(pathname)}` : "";
      router.replace(`/login${next}`);
    }
  }, [status, router, pathname]);

  if (status === "loading") {
    return <FullPageSpinner label="Loading your workspace…" />;
  }

  if (status === "unauthenticated") {
    // Redirect in flight.
    return <FullPageSpinner label="Redirecting to sign-in…" />;
  }

  if (!user) return null;

  if (!authorized) {
    return (
      <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center px-6 text-center">
        <span className="mb-4 flex size-12 items-center justify-center rounded-xl bg-amber-100">
          <ShieldAlert className="size-6 text-warning" />
        </span>
        <h1 className="text-lg font-semibold">You do not have access to this area</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This section is restricted to {roles?.length ? roles.join(" / ").toLowerCase().replace(/_/g, " ") : "authorized"} accounts.
          Your organization administrator controls access to these capabilities.
        </p>
        <Link
          href="/"
          className="mt-5 inline-flex h-9 items-center rounded-md bg-primary px-4 text-sm font-medium text-white shadow-sm hover:bg-primary/90"
        >
          Back to home
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
