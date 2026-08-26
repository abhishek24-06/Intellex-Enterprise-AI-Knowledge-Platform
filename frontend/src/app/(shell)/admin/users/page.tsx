import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { UsersView } from "@/components/users/users-view";

export const metadata: Metadata = {
  title: "Users",
};

export default function AdminUsersPage() {
  return (
    <RequireAuth roles={["ORG_ADMIN"]}>
      <UsersView />
    </RequireAuth>
  );
}
