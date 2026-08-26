import Link from "next/link";
import { ArrowLeft, ShieldAlert } from "lucide-react";

export const metadata = { title: "Unauthorized" };

export default function UnauthorizedPage() {
  return (
    <main className="flex min-h-screen flex-1 items-center justify-center px-6">
      <div className="max-w-md text-center">
        <span className="mx-auto mb-5 flex size-12 items-center justify-center rounded-xl bg-amber-100">
          <ShieldAlert className="size-6 text-warning" />
        </span>
        <h1 className="text-xl font-semibold">Access denied</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          You are not authorized to view this area. Frontend navigation is a
          convenience only — the Intellex backend enforces permissions for every
          request.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex h-9 items-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-white shadow-sm hover:bg-primary/90"
        >
          <ArrowLeft className="size-4" />
          Back to home
        </Link>
      </div>
    </main>
  );
}
