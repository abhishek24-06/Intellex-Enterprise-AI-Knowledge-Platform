import { apiFetch } from "./client";
import type {
  CreateTeamRequest,
  Team,
} from "@/types/api";

export function createTeam(
  payload: CreateTeamRequest,
): Promise<Team> {
  return apiFetch<Team>("/teams", {
    method: "POST",
    body: payload,
  });
}

export function listTeams(): Promise<Team[]> {
  return apiFetch<Team[]>("/teams");
}