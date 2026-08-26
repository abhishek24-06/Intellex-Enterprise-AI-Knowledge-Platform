import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { AdminDashboard } from "@/components/admin/admin-dashboard";

export const metadata: Metadata = {
  title: "Admin Overview",
};

export default function AdminPage() {
  return (
    <RequireAuth roles={["ORG_ADMIN"]}>
      <AdminDashboard />
    </RequireAuth>
  );
}
