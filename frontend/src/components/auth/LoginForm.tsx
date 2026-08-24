"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "@/src/lib/api";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

export default function LoginForm() {
  const router = useRouter();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleSubmit(
    event: FormEvent,
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const result =
        await apiFetch<LoginResponse>(
          "/auth/login",
          {
            method: "POST",
            auth: false,
            body: JSON.stringify({
              email,
              password,
            }),
          },
        );

      sessionStorage.setItem(
        "intellex_token",
        result.access_token,
      );

      router.push("/chat");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-8 shadow-2xl">
      <div className="mb-8">
        <div className="mb-3 text-3xl font-bold tracking-tight text-white">
          Intellex
        </div>

        <p className="text-sm text-zinc-400">
          Enterprise Knowledge Intelligence
        </p>
      </div>

      <button
        type="button"
        disabled
        className="mb-5 flex w-full items-center justify-center gap-3 rounded-xl border border-zinc-700 bg-zinc-800 px-4 py-3 text-sm font-medium text-zinc-400"
      >
        <span className="text-lg">
          G
        </span>
        Continue with Google
      </button>

      <div className="mb-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-zinc-800" />
        <span className="text-xs text-zinc-500">
          OR
        </span>
        <div className="h-px flex-1 bg-zinc-800" />
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-4"
      >
        <div>
          <label className="mb-2 block text-sm text-zinc-300">
            Email
          </label>

          <input
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value,
              )
            }
            required
            className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-white outline-none transition focus:border-white"
            placeholder="you@company.com"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm text-zinc-300">
            Password
          </label>

          <input
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value,
              )
            }
            required
            className="w-full rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-white outline-none transition focus:border-white"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="rounded-xl border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-white px-4 py-3 font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading
            ? "Signing in..."
            : "Sign in"}
        </button>
      </form>
    </div>
  );
}