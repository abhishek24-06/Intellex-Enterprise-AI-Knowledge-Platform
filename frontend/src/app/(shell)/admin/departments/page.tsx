import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { DepartmentsView } from "@/components/departments/departments-view";

export const metadata: Metadata = {
  title: "Departments",
};

export default function AdminDepartmentsPage() {
  return (
    <RequireAuth roles={["ORG_ADMIN"]}>
      <DepartmentsView />
    </RequireAuth>
  );
}
