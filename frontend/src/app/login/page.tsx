import type { Metadata } from "next";
import { Suspense } from "react";
import { BrainCircuit, Database, FileSearch, Lock } from "lucide-react";

import { LoginForm } from "@/components/auth/login-form";
import { APP_NAME } from "@/lib/config";

export const metadata: Metadata = {
  title: "Sign in",
};

const highlights = [
  {
    icon: FileSearch,
    title: "Agentic knowledge retrieval",
    description:
      "ACL-aware search across your organization's documents with reranked relevance.",
  },
  {
    icon: Database,
    title: "Structured enterprise answers",
    description:
      "Ask about people, teams, and departments — grounded in your org directory.",
  },
];

export default function LoginPage() {
  return (
    <main className="grid min-h-screen bg-background lg:grid-cols-[1.05fr_1fr]">
      {/* Brand panel */}
      <section className="relative hidden min-h-screen flex-col justify-between overflow-hidden bg-sidebar px-10 py-8 text-sidebar-foreground lg:flex xl:px-14">
        <div className="flex items-center gap-2.5">
          <BrandMark />
          <span className="text-lg font-semibold tracking-tight text-white">{APP_NAME}</span>
        </div>

        <div className="max-w-md space-y-8">
          <h2 className="max-w-xl text-4xl font-semibold leading-[1.08] tracking-[-0.02em] text-white xl:text-[2.75rem]">
            The Enterprise operating system for secure organizational
            knowledge&nbsp;and&nbsp;AI.
          </h2>
          <ul className="space-y-6">
            {highlights.map((item) => (
              <li key={item.title} className="flex gap-3.5">
                <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg bg-sidebar-accent ring-1 ring-sidebar-border">
                  <item.icon className="size-4.5 text-indigo-400" />
                </span>
                <div>
                  <p className="text-sm font-medium text-white">{item.title}</p>
                  <p className="mt-0.5 text-sm leading-relaxed text-sidebar-muted">
                    {item.description}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-sidebar-muted">
          © {new Date().getFullYear()} Intellex. All rights reserved.
        </p>
      </section>

      {/* Form panel */}
      <section className="flex items-center justify-center px-6 py-16 sm:px-12">
        <Suspense fallback={<LoginFormSkeleton />}>
          <LoginForm />
        </Suspense>
      </section>
    </main>
  );
}

function BrandMark() {
  return (
    <span className="flex size-9 items-center justify-center rounded-lg bg-indigo-600 shadow-inner">
      <BrainCircuit className="size-5 text-white" />
    </span>
  );
}

function LoginFormSkeleton() {
  return <div className="h-96 w-full max-w-sm animate-pulse rounded-lg bg-muted" />;
}
