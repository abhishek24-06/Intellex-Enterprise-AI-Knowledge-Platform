import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { DocumentsAdminView } from "@/components/documents/documents-admin-view";

export const metadata: Metadata = {
  title: "Documents",
};

export default function AdminDocumentsPage() {
  return (
    <RequireAuth roles={["ORG_ADMIN"]}>
      <DocumentsAdminView />
    </RequireAuth>
  );
}
