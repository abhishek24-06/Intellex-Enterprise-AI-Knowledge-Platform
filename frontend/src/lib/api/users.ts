import { apiFetch } from "./client";
import type {
  ChangeUserRoleRequest,
  CreateEmployeeRequest,
  CreateOrgAdminRequest,
  UpdateUserRequest,
  User,
} from "@/types/api";

export function listUsers(): Promise<User[]> {
  return apiFetch<User[]>("/users/");
}

export function getUser(userId: number): Promise<User> {
  return apiFetch<User>(`/users/${userId}`);
}

export function createEmployee(payload: CreateEmployeeRequest): Promise<User> {
  return apiFetch<User>("/users/employees", { method: "POST", body: payload });
}

export function createOrgAdmin(payload: CreateOrgAdminRequest): Promise<User> {
  return apiFetch<User>("/users/org-admins", { method: "POST", body: payload });
}

export function updateUser(userId: number, payload: UpdateUserRequest): Promise<User> {
  return apiFetch<User>(`/users/${userId}`, { method: "PATCH", body: payload });
}

export function changeUserRole(userId: number, payload: ChangeUserRoleRequest): Promise<User> {
  return apiFetch<User>(`/users/${userId}/role`, { method: "PATCH", body: payload });
}
