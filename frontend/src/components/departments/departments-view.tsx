"use client";

import * as React from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  FolderKanban,
  Info,
  Plus,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  EmptyState,
  ErrorState,
} from "@/components/shared/states";

import { PageHeader } from "@/components/layout/page-header";

import {
  createDepartment,
  listDepartments,
} from "@/lib/api/departments";

export function DepartmentsView() {
  const [name, setName] = React.useState("");
  const [description, setDescription] =
    React.useState("");
  const [error, setError] =
    React.useState<string | null>(null);

  const queryClient =
    useQueryClient();

  // ----------------------------------------------------------
  // Load departments
  // ----------------------------------------------------------

  const departmentsQuery =
    useQuery({
      queryKey: ["departments"],
      queryFn: listDepartments,
    });

  const departments =
    departmentsQuery.data ?? [];

  // ----------------------------------------------------------
  // Create department
  // ----------------------------------------------------------

  const mutation =
    useMutation({
      mutationFn: () =>
        createDepartment({
          name: name.trim(),
          description: description.trim(),
        }),

      onSuccess: (department) => {
        setName("");
        setDescription("");
        setError(null);

        void queryClient.invalidateQueries({
          queryKey: ["departments"],
        });

        toast.success(
          `Department “${department.name}” created`,
        );
      },

      onError: (err) => {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to create department.",
        );
      },
    });

  // ----------------------------------------------------------
  // Submit
  // ----------------------------------------------------------

  function onSubmit(
    event: React.FormEvent,
  ) {
    event.preventDefault();

    const trimmedName =
      name.trim();

    const trimmedDescription =
      description.trim();

    if (!trimmedName) {
      setError(
        "Department name is required.",
      );
      return;
    }

    if (!trimmedDescription) {
      setError(
        "Department description is required.",
      );
      return;
    }

    setError(null);

    mutation.mutate();
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-64px)] w-full min-w-0 max-w-6xl flex-col overflow-hidden p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Departments"
        description="Create organizational departments for structuring employees and document access."
      />

      <div className="grid min-h-0 min-w-0 flex-1 gap-6 lg:grid-cols-[420px_minmax(0,1fr)]">
        {/* =====================================================
            CREATE DEPARTMENT
           ===================================================== */}

        <Card className="lg:shrink-0">
          <CardHeader>
            <CardTitle className="text-base">
              New department
            </CardTitle>

            <CardDescription>
              Names should be unique and descriptive.
            </CardDescription>
          </CardHeader>

          <CardContent>
            <form
              onSubmit={onSubmit}
              className="space-y-4"
              noValidate
            >
              {error ? (
                <p
                  role="alert"
                  className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
                >
                  {error}
                </p>
              ) : null}

              {/* Name */}
              <label className="block space-y-1.5">
                <Label>
                  Name
                </Label>

                <Input
                  value={name}
                  onChange={(event) => {
                    setName(
                      event.target.value,
                    );

                    if (error) {
                      setError(null);
                    }
                  }}
                  placeholder="e.g. Engineering"
                  maxLength={100}
                />
              </label>

              {/* Description */}
              <label className="block space-y-1.5">
                <Label>
                  Description
                </Label>

                <Textarea
                  value={description}
                  onChange={(event) => {
                    setDescription(
                      event.target.value,
                    );

                    if (error) {
                      setError(null);
                    }
                  }}
                  placeholder="What does this department do?"
                  rows={3}
                  required
                />
              </label>

              <Button
                type="submit"
                disabled={mutation.isPending}
                className="w-full"
              >
                <Plus />

                {mutation.isPending
                  ? "Creating..."
                  : "Create department"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* =====================================================
            DEPARTMENT DIRECTORY
           ===================================================== */}

        <div className="flex min-h-0 min-w-0 flex-col">
          {/* Information banner */}
          <div className="mb-4 flex shrink-0 items-start gap-2 rounded-lg border border-indigo-200 bg-indigo-50/70 px-3.5 py-3 text-xs leading-relaxed text-indigo-900">
            <Info className="mt-0.5 size-4 shrink-0 text-indigo-500" />

            <span>
              Departments in your organization are
              shown here. Create a department using
              the form, then use it when creating
              teams or assigning employees.
            </span>
          </div>

          {/* Scrollable department directory */}
          <div className="min-h-0 flex-1 overflow-y-auto pr-2 [scrollbar-width:thin]">
            {departmentsQuery.isLoading ? (
              <div className="space-y-2.5">
                {[0, 1, 2].map(
                  (item) => (
                    <Card key={item}>
                      <CardContent className="p-4">
                        <div className="h-5 w-40 animate-pulse rounded bg-muted" />

                        <div className="mt-2 h-4 w-64 animate-pulse rounded bg-muted" />
                      </CardContent>
                    </Card>
                  ),
                )}
              </div>
            ) : departmentsQuery.isError ? (
              <ErrorState
                title="Unable to load departments"
                message="The department directory could not be loaded."
                onRetry={() =>
                  void departmentsQuery.refetch()
                }
              />
            ) : departments.length === 0 ? (
              <EmptyState
                icon={FolderKanban}
                title="No departments found"
                description="Create your first organizational department."
              />
            ) : (
              <ul className="min-w-0 space-y-2.5">
                {departments.map(
                  (department) => (
                    <li
                      key={
                        department.department_id
                      }
                    >
                      <Card className="min-w-0">
                        <CardContent className="min-w-0 p-4">
                          <div className="min-w-0">
                            <p className="text-sm font-medium">
                              {department.name}
                            </p>

                            <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                              {department.description}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    </li>
                  ),
                )}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}