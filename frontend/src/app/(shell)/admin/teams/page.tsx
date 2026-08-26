import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { TeamsView } from "@/components/teams/teams-view";

export const metadata: Metadata = {
  title: "Teams",
};

export default function AdminTeamsPage() {
  return (
    <RequireAuth roles={["ORG_ADMIN"]}>
      <TeamsView />
    </RequireAuth>
  );
}
