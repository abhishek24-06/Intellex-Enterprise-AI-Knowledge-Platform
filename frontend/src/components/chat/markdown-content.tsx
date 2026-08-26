"use client";

import * as React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Check, Copy } from "lucide-react";

import { cn } from "@/lib/utils";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = React.useState(false);

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard unavailable; ignore.
    }
  }

  return (
    <button
      type="button"
      onClick={onCopy}
      className="inline-flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs text-zinc-300 transition-colors hover:bg-zinc-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      aria-label="Copy code"
    >
      {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

/**
 * Renders assistant answers as sanitized markdown.
 * Only markdown produced by the API answer field is rendered — internal
 * reasoning or prompts are never displayed.
 */
export function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="space-y-3 text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-base font-semibold tracking-tight">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-[15px] font-semibold tracking-tight">{children}</h2>
          ),
          h3: ({ children }) => <h3 className="text-sm font-semibold">{children}</h3>,
          p: ({ children }) => <p className="leading-relaxed">{children}</p>,
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium underline underline-offset-4"
            >
              {children}
            </a>
          ),
          ul: ({ children }) => <ul className="ml-5 list-disc space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="ml-5 list-decimal space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-indigo-400/60 pl-3 italic opacity-90">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full text-left text-sm">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-muted/60 text-xs uppercase tracking-wide">{children}</thead>
          ),
          th: ({ children }) => <th className="border-b px-3 py-2 font-semibold">{children}</th>,
          td: ({ children }) => <td className="border-b px-3 py-2 last:border-b-0">{children}</td>,
          code: ({
            className,
            children,
            ...props
          }: React.HTMLAttributes<HTMLElement> & { inline?: boolean }) => {
            const raw = String(children ?? "");
            const isBlock =
              /language-/.test(className ?? "") || raw.includes("\n");

            if (!isBlock) {
              return (
                <code
                  className={cn(
                    "rounded bg-black/[0.06] px-1.5 py-0.5 font-mono text-[0.85em]",
                    className,
                  )}
                >
                  {children}
                </code>
              );
            }

            const language =
              /language-(\w+)/.exec(className ?? "")?.[1] ?? "code";

            return (
              <div className="overflow-hidden rounded-lg border border-zinc-700/50 bg-zinc-900">
                <div className="flex items-center justify-between border-b border-zinc-700/50 px-3 py-1.5">
                  <span className="text-xs font-medium text-zinc-400">{language}</span>
                  <CopyButton text={raw} />
                </div>
                <pre className="overflow-x-auto p-3 text-[13px] leading-relaxed text-zinc-100">
                  <code className={cn("font-mono", className)} {...props}>
                    {children}
                  </code>
                </pre>
              </div>
            );
          },
          pre: ({ children }) => <>{children}</>,
          hr: () => <hr className="border-border" />,
          strong: ({ children }) => (
            <strong className="font-semibold">{children}</strong>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
