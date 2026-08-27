"use client";

import * as React from "react";
import { Building2, FolderKanban, Mail, Network, ShieldCheck, UserRound } from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { useAuth } from "@/providers/auth-provider";

const ROLE_BADGE = {
  EMPLOYEE: { label: "Employee", variant: "secondary" },
  ORG_ADMIN: { label: "Organization Admin", variant: "info" },
  SUPER_ADMIN: { label: "Super Admin", variant: "warning" },
} as const;

function ProfileRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3 border-b py-3 last:border-b-0">
      <Icon className="size-4 shrink-0 text-muted-foreground" />
      <span className="w-32 shrink-0 text-sm text-muted-foreground">{label}</span>
      <span className="truncate font-mono text-sm">{value}</span>
    </div>
  );
}

export function ProfileView() {
  const { user, status } = useAuth();

  if (!user) return null;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader title="Profile" description="Your account details resolved from the platform." />

      <Card>
        <CardHeader className="flex-row items-center gap-4 space-y-0">
          <Avatar name={user.name} className="size-14 rounded-xl text-lg" />
          <div>
            <CardTitle>{user.name}</CardTitle>
            <CardDescription className="mt-1 flex items-center gap-2">
              <Mail className="inline size-3.5" />
              {user.email}
            </CardDescription>
            <Badge variant={ROLE_BADGE[user.role].variant} className="mt-2">
              <ShieldCheck className="size-3" />
              {ROLE_BADGE[user.role].label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <ProfileRow icon={UserRound} label="User ID" value={`#${user.user_id}`} />
          <ProfileRow
            icon={Building2}
            label="Organization"
            value={user.organization_id !== null ? `#${user.organization_id}` : "—"}
          />
          <ProfileRow
            icon={FolderKanban}
            label="Department"
            value={user.department_id !== null ? `#${user.department_id}` : "—"}
          />
          <ProfileRow
            icon={Network}
            label="Team"
            value={user.team_id !== null ? `#${user.team_id}` : "—"}
          />
        </CardContent>
      </Card>

      {/* <p className="text-xs leading-relaxed text-muted-foreground" aria-live="polite">
        {status === "authenticated"
          ? "Details are fetched live from GET /auth/me using your session token."
          : ""}
      </p> */}
    </div>
  );
}
