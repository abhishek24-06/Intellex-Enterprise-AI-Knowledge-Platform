import { apiFetch } from "./client";
import type { CreateTeamRequest, Team } from "@/types/api";

// The backend currently exposes only team creation (POST /teams).

export function createTeam(payload: CreateTeamRequest): Promise<Team> {
  return apiFetch<Team>("/teams", { method: "POST", body: payload });
}
