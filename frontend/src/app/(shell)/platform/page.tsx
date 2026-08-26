import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { PlatformView } from "@/components/admin/platform-view";

export const metadata: Metadata = {
  title: "Platform",
};

export default function PlatformPage() {
  return (
    <RequireAuth roles={["SUPER_ADMIN"]}>
      <PlatformView />
    </RequireAuth>
  );
}
