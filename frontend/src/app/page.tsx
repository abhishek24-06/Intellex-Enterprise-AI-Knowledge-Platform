"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

import { FullPageLoader } from "@/components/shared/full-page-loader";
import { useAuth } from "@/providers/auth-provider";
import type { UserRole } from "@/types/api";

function landingForRole(role: UserRole): string {
  switch (role) {
    case "ORG_ADMIN":
      return "/admin";
    case "SUPER_ADMIN":
      return "/platform";
    case "EMPLOYEE":
    default:
      return "/employee";
  }
}

export default function HomePage() {
  const { status, user } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
      return;
    }
    if (status === "authenticated" && user) {
      router.replace(landingForRole(user.role));
    }
  }, [status, user, router]);

  return <FullPageLoader label="Starting Intellex…" />;
}
