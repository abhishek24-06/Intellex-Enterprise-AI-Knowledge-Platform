"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { FolderKanban, Info, Plus } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import { createDepartment } from "@/lib/api/departments";
import { formatDateTime } from "@/lib/utils";
import type { Department } from "@/types/api";

/**
 * The backend currently exposes only department creation (POST /departments).
 * There is no listing endpoint yet, so this page shows departments created
 * during the current browser session only — clearly labeled as such.
 */
export function DepartmentsView() {
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [created, setCreated] = React.useState<Department[]>([]);

  const mutation = useMutation({
    mutationFn: () =>
      createDepartment({
        name: name.trim(),
        description: description.trim() || null,
      }),
    onSuccess: (department) => {
      setCreated((prev) => [department, ...prev]);
      setName("");
      setDescription("");
      setError(null);
      toast.success(`Department “${department.name}” created (#${department.department_id})`);
    },
    onError: (err) => setError(err.message),
  });

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Department name is required.");
      return;
    }
    mutation.mutate();
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Departments"
        description="Create organizational departments for structuring employees and document access."
      />

      <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">New department</CardTitle>
            <CardDescription>Names should be unique and descriptive.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              {error ? (
                <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {error}
                </p>
              ) : null}

              <label className="block space-y-1.5">
                <Label>Name</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Engineering"
                  maxLength={100}
                />
              </label>

              <label className="block space-y-1.5">
                <Label>Description</Label>
                <Textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What does this department do?"
                  rows={3}
                />
              </label>

              <Button type="submit" disabled={mutation.isPending} className="w-full">
                <Plus />
                Create department
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <div className="flex items-start gap-2 rounded-lg border border-indigo-200 bg-indigo-50/70 px-3.5 py-3 text-xs leading-relaxed text-indigo-900">
            <Info className="mt-0.5 size-4 shrink-0 text-indigo-500" />
            <span>
              The platform API currently supports creating departments only.
              A directory of all departments will appear here once a listing
              endpoint becomes available. Departments created in this session are
              shown below with their assigned IDs for reference.
            </span>
          </div>

          {created.length === 0 ? (
            <EmptyState
              icon={FolderKanban}
              title="No departments created in this session"
              description="Use the form to create your first department."
            />
          ) : (
            <ul className="space-y-2.5">
              {created.map((dept) => (
                <li key={dept.department_id}>
                  <Card>
                    <CardContent className="flex items-center justify-between gap-4 p-4">
                      <div className="min-w-0">
                        <p className="flex items-center gap-2 text-sm font-medium">
                          {dept.name}
                          <Badge variant="secondary">#{dept.department_id}</Badge>
                        </p>
                        <p className="mt-0.5 truncate text-xs text-muted-foreground">
                          {dept.description || "No description"}
                        </p>
                      </div>
                      <span className="shrink-0 font-mono text-xs text-muted-foreground">
                        {formatDateTime(dept.created_at)}
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
