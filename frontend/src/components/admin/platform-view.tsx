"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { Building2, CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { onboardOrganization } from "@/lib/api/organizations";
import type { OrganizationOnboardingResponse } from "@/types/api";

const INITIAL = {
  organization_name: "",
  industry_name: "",
  admin_name: "",
  admin_email: "",
  admin_password: "",
};

/**
 * SUPER_ADMIN console. The backend authorizes the platform administrator for
 * organization onboarding only — no other organization APIs are exposed, and
 * none are represented here.
 */
export function PlatformView() {
  const [form, setForm] = React.useState(INITIAL);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<OrganizationOnboardingResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () => onboardOrganization(form),
    onSuccess: (data) => {
      setResult(data);
      setForm(INITIAL);
      setError(null);
    },
    onError: (err) => setError(err.message),
  });

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!form.organization_name.trim()) return setError("Organization name is required.");
    if (!form.industry_name.trim()) return setError("Industry is required.");
    if (!form.admin_name.trim()) return setError("Administrator name is required.");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.admin_email.trim()))
      return setError("Enter a valid administrator email.");
    if (form.admin_password.length < 8)
      return setError("Administrator password must be at least 8 characters.");
    setError(null);
    mutation.mutate();
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Platform Administration"
        description="Onboard new organizations onto Intellex."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="size-4 text-primary" />
              Onboard organization
            </CardTitle>
            <CardDescription>
              Creates the organization and its first administrator account.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              {error ? (
                <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {error}
                </p>
              ) : null}

              <label className="block space-y-1.5">
                <Label>Organization name</Label>
                <Input
                  value={form.organization_name}
                  onChange={(e) => setForm((f) => ({ ...f, organization_name: e.target.value }))}
                  placeholder="Acme Corporation"
                />
              </label>

              <label className="block space-y-1.5">
                <Label>Industry</Label>
                <Input
                  value={form.industry_name}
                  onChange={(e) => setForm((f) => ({ ...f, industry_name: e.target.value }))}
                  placeholder="Manufacturing"
                />
              </label>

              <div className="rounded-lg border bg-muted/40 p-3">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  First administrator
                </p>
                <div className="space-y-3.5">
                  <label className="block space-y-1.5">
                    <Label>Name</Label>
                    <Input
                      value={form.admin_name}
                      onChange={(e) => setForm((f) => ({ ...f, admin_name: e.target.value }))}
                      placeholder="Alex Chen"
                    />
                  </label>
                  <label className="block space-y-1.5">
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={form.admin_email}
                      onChange={(e) => setForm((f) => ({ ...f, admin_email: e.target.value }))}
                      placeholder="alex@acme.com"
                    />
                  </label>
                  <label className="block space-y-1.5">
                    <Label>Temporary password</Label>
                    <Input
                      type="password"
                      value={form.admin_password}
                      onChange={(e) => setForm((f) => ({ ...f, admin_password: e.target.value }))}
                      placeholder="Minimum 8 characters"
                    />
                  </label>
                </div>
              </div>

              <Button type="submit" disabled={mutation.isPending} className="w-full">
                {mutation.isPending ? "Onboarding…" : "Onboard organization"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-4">
          {result ? (
            <Card className="border-emerald-200">
              <CardHeader className="flex-row items-start gap-3 space-y-0">
                <CheckCircle2 className="mt-1 size-5 shrink-0 text-emerald-600" />
                <div>
                  <CardTitle className="text-base">{result.message}</CardTitle>
                  <CardDescription>
                    Share these credentials securely with the new administrator.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <dl className="space-y-2 rounded-lg border bg-muted/40 p-4 text-sm">
                  <Row label="Organization" value={`${result.organization.name} (#${result.organization.organization_id})`} />
                  <Row label="Industry" value={result.organization.industry} />
                  <Row label="Status" value={result.organization.is_active ? "Active" : "Inactive"} />
                  <Row label="Admin email" value={result.admin_email} />
                </dl>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  The administrator can now sign in and begin creating departments,
                  teams, employees, and uploading documents.
                </p>
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Platform scope</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm leading-relaxed text-muted-foreground">
              <p>
                As the Intellex platform administrator you can onboard organizations
                and inspect AI observability across the platform.
              </p>
              <p>
                Organization-internal management — users, departments, teams, and
                documents — is performed by each organization&apos;s own admins.
              </p>
              <Badge variant="warning">Super Admin workspace</Badge>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}
