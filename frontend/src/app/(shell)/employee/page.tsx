import type { Metadata } from "next";

import { EmployeeDashboard } from "@/components/layout/employee-dashboard";

export const metadata: Metadata = {
  title: "Home",
};

export default function EmployeePage() {
  return <EmployeeDashboard />;
}
