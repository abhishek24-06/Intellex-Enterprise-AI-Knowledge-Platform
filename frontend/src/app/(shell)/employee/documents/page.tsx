import type { Metadata } from "next";

import { MyDocumentsView } from "@/components/documents/my-documents-view";

export const metadata: Metadata = {
  title: "My Documents",
};

export default function EmployeeDocumentsPage() {
  return <MyDocumentsView />;
}
