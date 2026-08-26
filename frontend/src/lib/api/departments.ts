import { apiFetch } from "./client";
import type {
  CreateDepartmentRequest,
  Department,
} from "@/types/api";

export function createDepartment(
  payload: CreateDepartmentRequest,
): Promise<Department> {
  return apiFetch<Department>(
    "/departments",
    {
      method: "POST",
      body: payload,
    },
  );
}

export function listDepartments(): Promise<
  Department[]
> {
  return apiFetch<Department[]>(
    "/departments",
  );
}