import { apiFetch } from "./client";
import type { CreateDepartmentRequest, Department } from "@/types/api";

// The backend currently exposes only department creation (POST /departments).
// List/get/update/delete endpoints do not exist yet and must not be fabricated.

export function createDepartment(payload: CreateDepartmentRequest): Promise<Department> {
  return apiFetch<Department>("/departments", { method: "POST", body: payload });
}
