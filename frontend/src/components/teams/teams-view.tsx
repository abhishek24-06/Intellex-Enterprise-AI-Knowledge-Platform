"use client";

import * as React from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  Info,
  Network,
  Plus,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
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
  createTeam,
  listTeams,
} from "@/lib/api/teams";

import { listDepartments } from "@/lib/api/departments";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export function TeamsView() {
  const [departmentId, setDepartmentId] =
    React.useState("");

  const [name, setName] =
    React.useState("");

  const [description, setDescription] =
    React.useState("");

  const [error, setError] =
    React.useState<string | null>(null);

  const queryClient =
    useQueryClient();

  // ----------------------------------------------------------
  // Departments
  // ----------------------------------------------------------

  const departmentsQuery =
    useQuery({
      queryKey: ["departments"],
      queryFn: listDepartments,
    });

  const departments =
    departmentsQuery.data ?? [];

  // ----------------------------------------------------------
  // Department lookup
  // ----------------------------------------------------------

  const departmentNameById =
    new Map(
      departments.map(
        (department) => [
          department.department_id,
          department.name,
        ],
      ),
    );

  // ----------------------------------------------------------
  // Teams
  // ----------------------------------------------------------

  const teamsQuery =
    useQuery({
      queryKey: ["teams"],
      queryFn: listTeams,
    });

  const teams =
    teamsQuery.data ?? [];

  // ----------------------------------------------------------
  // Create team
  // ----------------------------------------------------------

  const mutation =
    useMutation({
      mutationFn: () =>
        createTeam({
          department_id:
            Number(departmentId),

          name:
            name.trim(),

          description:
            description.trim(),
        }),

      onSuccess: (team) => {
        setDepartmentId("");
        setName("");
        setDescription("");
        setError(null);

        void queryClient.invalidateQueries({
          queryKey: ["teams"],
        });

        toast.success(
          `Team “${team.name}” created`,
        );
      },

      onError: (err) => {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to create team.",
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

    if (!departmentId) {
      setError(
        "Please select a department.",
      );
      return;
    }

    if (!name.trim()) {
      setError(
        "Team name is required.",
      );
      return;
    }

    if (!description.trim()) {
      setError(
        "Team description is required.",
      );
      return;
    }

    setError(null);

    mutation.mutate();
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-64px)] w-full min-w-0 max-w-6xl flex-col overflow-hidden p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Teams"
        description="Teams belong to departments and group employees for access and context."
      />

      <div className="grid min-h-0 min-w-0 flex-1 gap-6 lg:grid-cols-[420px_minmax(0,1fr)]">
        {/* =====================================================
            CREATE TEAM
           ===================================================== */}

        <Card className="lg:shrink-0">
          <CardHeader>
            <CardTitle className="text-base">
              New team
            </CardTitle>

            <CardDescription>
              Select an existing department for the
              new team.
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

              {/* Department */}
              <div className="space-y-1.5">
                <Label>
                  Department
                </Label>

                <Select
                  value={departmentId}
                  onValueChange={(value) => {
                    setDepartmentId(value);
                    setError(null);
                  }}
                  disabled={
                    departmentsQuery.isLoading ||
                    departmentsQuery.isError
                  }
                >
                  <SelectTrigger>
                    <SelectValue
                      placeholder={
                        departmentsQuery.isLoading
                          ? "Loading departments..."
                          : "Select a department"
                      }
                    />
                  </SelectTrigger>

                  <SelectContent>
                    {departments.map(
                      (department) => (
                        <SelectItem
                          key={
                            department.department_id
                          }
                          value={String(
                            department.department_id,
                          )}
                        >
                          {department.name}
                        </SelectItem>
                      ),
                    )}
                  </SelectContent>
                </Select>

                {departmentsQuery.isError ? (
                  <p className="text-xs text-red-600">
                    Unable to load departments.
                  </p>
                ) : null}
              </div>

              {/* Team name */}
              <label className="block space-y-1.5">
                <Label>
                  Team name
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
                  placeholder="e.g. Platform Engineering"
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
                  placeholder="What does this team own?"
                  rows={3}
                  required
                />
              </label>

              <Button
                type="submit"
                disabled={
                  mutation.isPending ||
                  departmentsQuery.isLoading ||
                  departmentsQuery.isError
                }
                className="w-full"
              >
                <Plus />

                {mutation.isPending
                  ? "Creating..."
                  : "Create team"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* =====================================================
            TEAM DIRECTORY
           ===================================================== */}

        <div className="flex min-h-0 min-w-0 flex-col">
          {/* Information banner */}
          <div className="mb-4 flex shrink-0 items-start gap-2 rounded-lg border border-indigo-200 bg-indigo-50/70 px-3.5 py-3 text-xs leading-relaxed text-indigo-900">
            <Info className="mt-0.5 size-4 shrink-0 text-indigo-500" />

            <span>
              Teams in your organization are shown
              here. Select a department when creating
              a new team.
            </span>
          </div>

          {/* Scrollable team directory */}
          <div className="min-h-0 flex-1 overflow-y-auto pr-2 [scrollbar-width:thin]">
            {teamsQuery.isLoading ? (
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
            ) : teamsQuery.isError ? (
              <ErrorState
                title="Unable to load teams"
                message="The team directory could not be loaded."
                onRetry={() =>
                  void teamsQuery.refetch()
                }
              />
            ) : teams.length === 0 ? (
              <EmptyState
                icon={Network}
                title="No teams found"
                description="Create your first organizational team."
              />
            ) : (
              <ul className="min-w-0 space-y-2.5">
                {teams.map((team) => {
                  const departmentName =
                    departmentNameById.get(
                      team.department_id,
                    );

                  return (
                    <li
                      key={team.team_id}
                    >
                      <Card className="min-w-0">
                        <CardContent className="min-w-0 p-4">
                          <div className="min-w-0">
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-sm font-medium">
                                {team.name}
                              </p>

                              {departmentName ? (
                                <Badge
                                  variant="secondary"
                                  className="font-normal"
                                >
                                  {departmentName}
                                </Badge>
                              ) : null}
                            </div>

                            <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                              {team.description}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}