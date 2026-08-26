"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";
import {
  Bot,
  BrainCircuit,
  Building2,
  FileText,
  FolderKanban,
  Gauge,
  LayoutDashboard,
  LogOut,
  type LucideIcon,
  Menu,
  MessagesSquare,
  Network,
  Search,
  ShieldCheck,
  UserRound,
  Users,
  X,
} from "lucide-react";

import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { APP_NAME } from "@/lib/config";
import { cn } from "@/lib/utils";
import { useAuth } from "@/providers/auth-provider";
import type { UserRole } from "@/types/api";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

interface NavSection {
  heading?: string;
  items: NavItem[];
}

function navForRole(role: UserRole): NavSection[] {
  if (role === "ORG_ADMIN") {
    return [
      {
        items: [{ label: "Overview", href: "/admin", icon: LayoutDashboard }],
      },
      {
        heading: "Workspace",
        items: [
          { label: "Chat", href: "/chat", icon: MessagesSquare },
          { label: "My Documents", href: "/admin/my-documents", icon: FileText },
        ],
      },
      {
        heading: "Organization",
        items: [
          { label: "Users", href: "/admin/users", icon: Users },
          { label: "Departments", href: "/admin/departments", icon: FolderKanban },
          { label: "Teams", href: "/admin/teams", icon: Network },
          { label: "Documents", href: "/admin/documents", icon: FileText },
        ],
      },
      {
        heading: "Intelligence",
        items: [{ label: "Observability", href: "/admin/observability", icon: Gauge }],
      },
    ];
  }

  if (role === "SUPER_ADMIN") {
    return [
      {
        items: [{ label: "Platform", href: "/platform", icon: Building2 }],
      },
      {
        heading: "Intelligence",
        items: [{ label: "Observability", href: "/admin/observability", icon: Gauge }],
      },
      {
        heading: "Workspace",
        items: [{ label: "Chat", href: "/chat", icon: MessagesSquare }],
      },
    ];
  }

  return [
    {
      items: [{ label: "Home", href: "/employee", icon: LayoutDashboard }],
    },
    {
      heading: "Workspace",
      items: [
        { label: "Chat", href: "/chat", icon: MessagesSquare },
        { label: "My Documents", href: "/employee/documents", icon: FileText },
      ],
    },
    {
      heading: "Account",
      items: [{ label: "Profile", href: "/employee/profile", icon: UserRound }],
    },
  ];
}

const ROLE_BADGE: Record<UserRole, { label: string; variant: "info" | "warning" | "secondary" }> = {
  EMPLOYEE: { label: "Employee", variant: "secondary" },
  ORG_ADMIN: { label: "Org Admin", variant: "info" },
  SUPER_ADMIN: { label: "Super Admin", variant: "warning" },
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const role = user?.role ?? "EMPLOYEE";
  const sections = React.useMemo(() => navForRole(role), [role]);

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  const sidebar = (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 shrink-0 items-center gap-2.5 border-b border-sidebar-border px-4">
        <span className="flex size-8 items-center justify-center rounded-lg bg-indigo-600">
          <BrainCircuit className="size-4.5 text-white" />
        </span>
        <span className="text-[15px] font-semibold tracking-tight text-white">{APP_NAME}</span>
      </div>

      <nav aria-label="Primary" className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {sections.map((section, index) => (
          <div key={section.heading ?? index} className="space-y-1">
            {section.heading ? (
              <p className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">
                {section.heading}
              </p>
            ) : null}
            {section.items.map((item) => {
              const active = isActive(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  onClick={() => setMobileOpen(false)}
                  className={cn(
                    "flex items-center gap-2.5 rounded-md px-2 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-sidebar-active text-white"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white",
                  )}
                >
                  <item.icon
                    className={cn("size-4 shrink-0", active ? "text-indigo-400" : "text-sidebar-muted")}
                  />
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        {user ? (
          <div className="flex items-center gap-2.5 rounded-md px-1 py-1">
            <Avatar name={user.name} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">{user.name}</p>
              <p className="truncate text-xs text-sidebar-muted">{user.email}</p>
            </div>
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-sidebar-muted hover:bg-sidebar-accent hover:text-white"
              onClick={logout}
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut className="size-4" />
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen flex-1">
      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-60 lg:block">{sidebar}</aside>

      {/* Mobile sidebar */}
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileOpen(false)}
            aria-hidden
          />
          <div className="absolute inset-y-0 left-0 w-64 shadow-xl">
            <button
              type="button"
              className="absolute right-3 top-4 z-10 rounded-md p-1 text-sidebar-muted hover:text-white"
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation"
            >
              <X className="size-5" />
            </button>
            {sidebar}
          </div>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col lg:pl-60">
        {/* Topbar (mobile actions + identity on desktop) */}
        <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center justify-between border-b bg-card/95 px-4 backdrop-blur sm:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation"
            >
              <Menu className="size-5" />
            </Button>
            <span className="flex items-center gap-2 lg:hidden">
              <Bot className="size-4 text-primary" />
              <span className="font-semibold">{APP_NAME}</span>
            </span>
          </div>

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <Avatar name={user.name} className="size-7" />
                  <span className="hidden text-left sm:block">
                    <span className="block text-sm font-medium leading-tight">{user.name}</span>
                    <span className="block text-xs text-muted-foreground leading-tight">
                      {ROLE_BADGE[user.role].label}
                    </span>
                  </span>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64">
                <DropdownMenuLabel>Signed in as</DropdownMenuLabel>
                <div className="px-2 pb-2">
                  <p className="truncate text-sm font-medium">{user.name}</p>
                  <p className="truncate text-xs text-muted-foreground">{user.email}</p>
                  <Badge variant={ROLE_BADGE[user.role].variant} className="mt-2">
                    <ShieldCheck className="size-3" />
                    {ROLE_BADGE[user.role].label}
                  </Badge>
                </div>
                <DropdownMenuSeparator />
                {(user.role === "EMPLOYEE" || user.role === "ORG_ADMIN") && (
                  <DropdownMenuItem asChild>
                    <Link href="/employee/profile">
                      <UserRound />
                      Profile
                    </Link>
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem destructive onSelect={() => logout()}>
                  <LogOut />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : null}
        </header>

        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
