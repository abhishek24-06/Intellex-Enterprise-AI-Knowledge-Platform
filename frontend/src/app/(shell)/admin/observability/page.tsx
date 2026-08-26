import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { ObservabilityView } from "@/components/observability/observability-view";

export const metadata: Metadata = {
  title: "Observability",
};

// Mirrors require_observability_admin on the backend.
export default function AdminObservabilityPage() {
  return (
    <RequireAuth roles={["ORG_ADMIN", "SUPER_ADMIN"]}>
      <ObservabilityView />
    </RequireAuth>
  );
}
