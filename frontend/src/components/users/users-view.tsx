"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  EllipsisVertical,
  Search,
  ShieldCheck,
  UserPlus,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { PageHeader } from "@/components/layout/page-header";
import {
  changeUserRole,
  createEmployee,
  createOrgAdmin,
  listUsers,
  updateUser,
} from "@/lib/api/users";
import type { User, UserRole } from "@/types/api";

const ROLE_BADGE: Record<UserRole, { label: string; variant: "info" | "warning" | "secondary" }> = {
  EMPLOYEE: { label: "Employee", variant: "secondary" },
  ORG_ADMIN: { label: "Org Admin", variant: "info" },
  SUPER_ADMIN: { label: "Super Admin", variant: "warning" },
};

// ---------------------------------------------------------------------------
// Create dialogs
// ---------------------------------------------------------------------------

interface CredentialFormState {
  name: string;
  email: string;
  password: string;
  departmentId: string;
  teamId: string;
}

const EMPTY_CREDENTIALS: CredentialFormState = {
  name: "",
  email: "",
  password: "",
  departmentId: "",
  teamId: "",
};

function validateCredentials(form: Pick<CredentialFormState, "name" | "email" | "password">): string | null {
  if (!form.name.trim()) return "Name is required.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) return "Enter a valid email address.";
  if (form.password.length < 8) return "Password must be at least 8 characters.";
  return null;
}

export function UsersView() {
  const queryClient = useQueryClient();

  const [query, setQuery] = React.useState("");
  const [roleFilter, setRoleFilter] = React.useState<UserRole | "all">("all");

  const [createEmployeeOpen, setCreateEmployeeOpen] = React.useState(false);
  const [createAdminOpen, setCreateAdminOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<User | null>(null);
  const [roleChanging, setRoleChanging] = React.useState<User | null>(null);
  const [viewing, setViewing] = React.useState<User | null>(null);

  const [employeeForm, setEmployeeForm] =
    React.useState<CredentialFormState>(EMPTY_CREDENTIALS);
  const [adminForm, setAdminForm] = React.useState({
    name: "",
    email: "",
    password: "",
  });
  const [editForm, setEditForm] = React.useState({ name: "", email: "", departmentId: "", teamId: "" });
  const [newRole, setNewRole] = React.useState<UserRole>("EMPLOYEE");
  const [dialogError, setDialogError] = React.useState<string | null>(null);

  const usersQuery = useQuery({ queryKey: ["users"], queryFn: listUsers });

  function invalidateUsers() {
    void queryClient.invalidateQueries({ queryKey: ["users"] });
  }

  const createEmployeeMutation = useMutation({
    mutationFn: () =>
      createEmployee({
        name: employeeForm.name.trim(),
        email: employeeForm.email.trim(),
        password: employeeForm.password,
        department_id: employeeForm.departmentId ? Number(employeeForm.departmentId) : null,
        team_id: employeeForm.teamId ? Number(employeeForm.teamId) : null,
      }),
    onSuccess: async () => {
      await invalidateUsers();
      setCreateEmployeeOpen(false);
      setEmployeeForm(EMPTY_CREDENTIALS);
      setDialogError(null);
      toast.success("Employee created");
    },
    onError: (error) => setDialogError(error.message),
  });

  const createOrgAdminMutation = useMutation({
    mutationFn: () =>
      createOrgAdmin({
        name: adminForm.name.trim(),
        email: adminForm.email.trim(),
        password: adminForm.password,
      }),
    onSuccess: () => {
      invalidateUsers();
      setCreateAdminOpen(false);
      setAdminForm({ name: "", email: "", password: "" });
      setDialogError(null);
      toast.success("Organization admin created");
    },
    onError: (error) => setDialogError(error.message),
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editing) throw new Error("No user selected");
      return updateUser(editing.user_id, {
        name: editForm.name.trim() || null,
        email: editForm.email.trim() || null,
        department_id: editForm.departmentId ? Number(editForm.departmentId) : null,
        team_id: editForm.teamId ? Number(editForm.teamId) : null,
      });
    },
    onSuccess: () => {
      invalidateUsers();
      setEditing(null);
      setDialogError(null);
      toast.success("User updated");
    },
    onError: (error) => setDialogError(error.message),
  });

  const roleMutation = useMutation({
    mutationFn: () => {
      if (!roleChanging) throw new Error("No user selected");
      return changeUserRole(roleChanging.user_id, { role: newRole });
    },
    onSuccess: () => {
      invalidateUsers();
      setRoleChanging(null);
      setDialogError(null);
      toast.success("Role updated");
    },
    onError: (error) => setDialogError(error.message),
  });

  const users = React.useMemo(() => usersQuery.data ?? [], [usersQuery.data]);
  const normalized = query.trim().toLowerCase();

  const filtered = React.useMemo(() => {
    let result = users;
    if (normalized) {
      result = result.filter(
        (user) =>
          user.name.toLowerCase().includes(normalized) ||
          user.email.toLowerCase().includes(normalized),
      );
    }
    if (roleFilter !== "all") {
      result = result.filter((user) => user.role === roleFilter);
    }
    return result;
  }, [users, normalized, roleFilter]);

  function openEdit(user: User) {
    setEditForm({
      name: user.name,
      email: user.email,
      departmentId: user.department_id !== null ? String(user.department_id) : "",
      teamId: user.team_id !== null ? String(user.team_id) : "",
    });
    setDialogError(null);
    setEditing(user);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Users"
        description="Manage the people in your organization."
        actions={
          <>
            <Button size="sm" onClick={() => { setEmployeeForm(EMPTY_CREDENTIALS); setDialogError(null); setCreateEmployeeOpen(true); }}>
              <UserPlus />
              Create Employee
            </Button>
            <Button size="sm" variant="outline" onClick={() => { setAdminForm({ name: "", email: "", password: "" }); setDialogError(null); setCreateAdminOpen(true); }}>
              <ShieldCheck />
              Create Org Admin
            </Button>
          </>
        }
      />

      {usersQuery.isLoading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : usersQuery.isError ? (
        <ErrorState
          title="Could not load users"
          message={usersQuery.error instanceof Error ? usersQuery.error.message : undefined}
          onRetry={() => usersQuery.refetch()}
        />
      ) : (
        <>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative max-w-xs flex-1">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by name or email…"
                className="pl-8"
                aria-label="Search users"
              />
            </div>
            <Select value={roleFilter} onValueChange={(value) => setRoleFilter(value as UserRole | "all")}>
              <SelectTrigger className="sm:w-44" aria-label="Filter by role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All roles</SelectItem>
                <SelectItem value="EMPLOYEE">Employees</SelectItem>
                <SelectItem value="ORG_ADMIN">Org Admins</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground sm:ml-auto">
              {filtered.length} of {users.length}
            </p>
          </div>

          {filtered.length === 0 ? (
            <EmptyState
              icon={Users}
              title={users.length === 0 ? "No active users yet" : "No matching users"}
              description={
                users.length === 0
                  ? "Create your first employee or organization admin to get started."
                  : "Adjust your search or filters to find who you're looking for."
              }
            />
          ) : (
            <div className="rounded-lg border bg-card shadow-sm">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Team</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead className="w-12"><span className="sr-only">Actions</span></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((user) => (
                    <TableRow key={user.user_id}>
                      <TableCell>
                        <p className="font-medium">{user.name}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                      </TableCell>
                      <TableCell>
                        <Badge variant={ROLE_BADGE[user.role].variant}>
                          {ROLE_BADGE[user.role].label}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        {user.department_id ?? "—"}
                      </TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        {user.team_id ?? "—"}
                      </TableCell>
                      <TableCell>
                        {user.is_active ? (
                          <Badge variant="success">Active</Badge>
                        ) : (
                          <Badge variant="secondary">Inactive</Badge>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-sm text-muted-foreground">
                        #{user.user_id}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon-sm" aria-label={`Actions for ${user.name}`}>
                              <EllipsisVertical className="size-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onSelect={() => setViewing(user)}>
                              View details
                            </DropdownMenuItem>
                            <DropdownMenuItem onSelect={() => openEdit(user)}>
                              Edit user
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onSelect={() => {
                                setRoleChanging(user);
                                setNewRole(user.role === "ORG_ADMIN" ? "EMPLOYEE" : "ORG_ADMIN");
                                setDialogError(null);
                              }}
                            >
                              Change role…
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}

          <p className="text-xs leading-relaxed text-muted-foreground">
            Note: the backend does not yet expose listing endpoints for departments
            or teams, so they are referenced by numeric ID. IDs are visible in the
            Departments and Teams pages after creation.
          </p>
        </>
      )}

      {/* ---------------- Create Employee ---------------- */}
      <Dialog open={createEmployeeOpen} onOpenChange={(open) => !open && setCreateEmployeeOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create employee</DialogTitle>
            <DialogDescription>
              Employees must belong to a department and a team.
            </DialogDescription>
          </DialogHeader>

          {dialogError ? (
            <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {dialogError}
            </p>
          ) : null}

          <div className="space-y-3.5">
            <Field label="Full name">
              <Input
                value={employeeForm.name}
                onChange={(e) => setEmployeeForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Enter Name"
              />
            </Field>
            <Field label="Email">
              <Input
                type="email"
                value={employeeForm.email}
                onChange={(e) => setEmployeeForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="Enter Company Email"
              />
            </Field>
            <Field label="Temporary password">
              <Input
                type="password"
                value={employeeForm.password}
                onChange={(e) => setEmployeeForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="Minimum 8 characters"
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Department ID">
                <Input
                  inputMode="numeric"
                  value={employeeForm.departmentId}
                  onChange={(e) => setEmployeeForm((f) => ({ ...f, departmentId: e.target.value.replace(/\D/g, "") }))}
                  placeholder="e.g. 1"
                />
              </Field>
              <Field label="Team ID">
                <Input
                  inputMode="numeric"
                  value={employeeForm.teamId}
                  onChange={(e) => setEmployeeForm((f) => ({ ...f, teamId: e.target.value.replace(/\D/g, "") }))}
                  placeholder="e.g. 2"
                />
              </Field>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateEmployeeOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={createEmployeeMutation.isPending}
              onClick={() => {
                const error = validateCredentials(employeeForm);
                if (error) {
                  setDialogError(error);
                  return;
                }
                createEmployeeMutation.mutate();
              }}
            >
              Create employee
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---------------- Create Org Admin ---------------- */}
      <Dialog open={createAdminOpen} onOpenChange={(open) => !open && setCreateAdminOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create organization admin</DialogTitle>
            <DialogDescription>
              Org admins manage users, structure, documents, and observability for this organization.
            </DialogDescription>
          </DialogHeader>

          {dialogError ? (
            <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {dialogError}
            </p>
          ) : null}

          <div className="space-y-3.5">
            <Field label="Full name">
              <Input
                value={adminForm.name}
                onChange={(e) => setAdminForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Alex Chen"
              />
            </Field>
            <Field label="Email">
              <Input
                type="email"
                value={adminForm.email}
                onChange={(e) => setAdminForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="alex@company.com"
              />
            </Field>
            <Field label="Temporary password">
              <Input
                type="password"
                value={adminForm.password}
                onChange={(e) => setAdminForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="Minimum 8 characters"
              />
            </Field>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateAdminOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={createOrgAdminMutation.isPending}
              onClick={() => {
                const error = validateCredentials(adminForm);
                if (error) {
                  setDialogError(error);
                  return;
                }
                createOrgAdminMutation.mutate();
              }}
            >
              Create org admin
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---------------- Edit User ---------------- */}
      <Dialog open={editing !== null} onOpenChange={(open) => !open && setEditing(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit user</DialogTitle>
            <DialogDescription>
              Update profile details and organizational placement.
            </DialogDescription>
          </DialogHeader>

          {dialogError ? (
            <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {dialogError}
            </p>
          ) : null}

          <div className="space-y-3.5">
            <Field label="Full name">
              <Input
                value={editForm.name}
                onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
              />
            </Field>
            <Field label="Email">
              <Input
                type="email"
                value={editForm.email}
                onChange={(e) => setEditForm((f) => ({ ...f, email: e.target.value }))}
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Department ID">
                <Input
                  inputMode="numeric"
                  value={editForm.departmentId}
                  onChange={(e) => setEditForm((f) => ({ ...f, departmentId: e.target.value.replace(/\D/g, "") }))}
                  placeholder={editing?.department_id !== null ? String(editing?.department_id) : "—"}
                />
              </Field>
              <Field label="Team ID">
                <Input
                  inputMode="numeric"
                  value={editForm.teamId}
                  onChange={(e) => setEditForm((f) => ({ ...f, teamId: e.target.value.replace(/\D/g, "") }))}
                  placeholder={editing?.team_id !== null ? String(editing?.team_id) : "—"}
                />
              </Field>
            </div>
            <p className="text-xs text-muted-foreground">
              Changing a department requires selecting a team that belongs to it.
              Leave both blank to keep current placement.
            </p>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button disabled={updateMutation.isPending} onClick={() => updateMutation.mutate()}>
              Save changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---------------- Change Role ---------------- */}
      <Dialog open={roleChanging !== null} onOpenChange={(open) => !open && setRoleChanging(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Change role</DialogTitle>
            <DialogDescription>
              {roleChanging ? `${roleChanging.name} · ${roleChanging.email}` : ""}
            </DialogDescription>
          </DialogHeader>

          {dialogError ? (
            <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
              {dialogError}
            </p>
          ) : null}

          <Select value={newRole} onValueChange={(value) => setNewRole(value as UserRole)}>
            <SelectTrigger aria-label="New role">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="EMPLOYEE">Employee</SelectItem>
              <SelectItem value="ORG_ADMIN">Organization Admin</SelectItem>
            </SelectContent>
          </Select>

          <p className="text-xs leading-relaxed text-muted-foreground">
            Demoting an org admin to employee requires existing department and team
            membership; promoting an admin clears their department and team.
          </p>

          <DialogFooter>
            <Button variant="outline" onClick={() => setRoleChanging(null)}>
              Cancel
            </Button>
            <Button disabled={roleMutation.isPending} onClick={() => roleMutation.mutate()}>
              Update role
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---------------- View details ---------------- */}
      <Dialog open={viewing !== null} onOpenChange={(open) => !open && setViewing(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{viewing?.name}</DialogTitle>
            <DialogDescription>{viewing?.email}</DialogDescription>
          </DialogHeader>
          {viewing ? (
            <dl className="space-y-2 rounded-lg border bg-muted/40 p-4 text-sm">
              <Row label="User ID" value={`#${viewing.user_id}`} />
              <Row label="Role" value={ROLE_BADGE[viewing.role].label} />
              <Row label="Status" value={viewing.is_active ? "Active" : "Inactive"} />
              <Row
                label="Department"
                value={viewing.department_id !== null ? `#${viewing.department_id}` : "—"}
              />
              <Row label="Team" value={viewing.team_id !== null ? `#${viewing.team_id}` : "—"} />
              <Row
                label="Organization"
                value={viewing.organization_id !== null ? `#${viewing.organization_id}` : "—"}
              />
            </dl>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <Label>{label}</Label>
      {children}
    </label>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}
