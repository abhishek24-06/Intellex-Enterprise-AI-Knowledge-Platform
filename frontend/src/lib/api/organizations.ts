import { apiFetch } from "./client";
import type { CreateOrganizationRequest, OrganizationOnboardingResponse } from "@/types/api";

// SUPER_ADMIN only. The backend exposes only organization onboarding.

export function onboardOrganization(
  payload: CreateOrganizationRequest,
): Promise<OrganizationOnboardingResponse> {
  return apiFetch<OrganizationOnboardingResponse>("/organizations", {
    method: "POST",
    body: payload,
  });
}
