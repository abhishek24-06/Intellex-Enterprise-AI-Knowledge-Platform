"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { Info, Network, Plus } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import { createTeam } from "@/lib/api/teams";
import { formatDateTime } from "@/lib/utils";
import type { Team } from "@/types/api";

/**
 * The backend currently exposes only team creation (POST /teams).
 * No listing endpoint exists yet; session-created teams are shown for reference.
 */
export function TeamsView() {
  const [departmentId, setDepartmentId] = React.useState("");
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [created, setCreated] = React.useState<Team[]>([]);

  const mutation = useMutation({
    mutationFn: () =>
      createTeam({
        department_id: Number(departmentId),
        name: name.trim(),
        description: description.trim() || null,
      }),
    onSuccess: (team) => {
      setCreated((prev) => [team, ...prev]);
      setName("");
      setDescription("");
      setError(null);
      toast.success(`Team “${team.name}” created (#${team.team_id})`);
    },
    onError: (err) => setError(err.message),
  });

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!departmentId) {
      setError("A department ID is required.");
      return;
    }
    if (!name.trim()) {
      setError("Team name is required.");
      return;
    }
    mutation.mutate();
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Teams"
        description="Teams belong to departments and group employees for access and context."
      />

      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">New team</CardTitle>
            <CardDescription>Reference an existing department ID.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              {error ? (
                <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {error}
                </p>
              ) : null}

              <label className="block space-y-1.5">
                <Label>Department ID</Label>
                <Input
                  inputMode="numeric"
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value.replace(/\D/g, ""))}
                  placeholder="e.g. 1"
                />
              </label>

              <label className="block space-y-1.5">
                <Label>Team name</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Platform Engineering"
                  maxLength={100}
                />
              </label>

              <label className="block space-y-1.5">
                <Label>Description</Label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What does this team own?"
                  rows={3}
                />
              </label>

              <Button type="submit" disabled={mutation.isPending} className="w-full">
                <Plus />
                Create team
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <div className="flex items-start gap-2 rounded-lg border border-indigo-200 bg-indigo-50/70 px-3.5 py-3 text-xs leading-relaxed text-indigo-900">
            <Info className="mt-0.5 size-4 shrink-0 text-indigo-500" />
            <span>
              The platform API currently supports creating teams only. Department IDs are
              shown on the Departments page after you create them. Teams created in this
              session appear below.
            </span>
          </div>

          {created.length === 0 ? (
            <EmptyState
              icon={Network}
              title="No teams created in this session"
              description="Use the form to create your first team."
            />
          ) : (
            <ul className="space-y-2.5">
              {created.map((team) => (
                <li key={team.team_id}>
                  <Card>
                    <CardContent className="flex items-center justify-between gap-4 p-4">
                      <div className="min-w-0">
                        <p className="flex flex-wrap items-center gap-2 text-sm font-medium">
                          {team.name}
                          <Badge variant="secondary">#{team.team_id}</Badge>
                          <Badge variant="outline">Dept #{team.department_id}</Badge>
                        </p>
                        <p className="mt-0.5 truncate text-xs text-muted-foreground">
                          {team.description || "No description"}
                        </p>
                      </div>
                      <span className="shrink-0 font-mono text-xs text-muted-foreground">
                        {formatDateTime(team.created_at)}
                      </span>
                    </CardContent>
                  </Card>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
