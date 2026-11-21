import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "InsightForge — Enterprise AI Data Analysis",
  description: "Ask questions of your data. Verified SQL, charts, and evidence.",
};

function NavLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
    >
      {label}
    </Link>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-200 dark:border-slate-800">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
              <Link href="/" className="text-lg font-bold tracking-tight">
                InsightForge
              </Link>
              <nav className="flex flex-wrap items-center gap-1">
                <NavLink href="/datasets" label="Datasets" />
                <NavLink href="/analysis" label="Analysis" />
                <NavLink href="/insights" label="Insights" />
                <NavLink href="/reports" label="Reports" />
                <NavLink href="/evaluations" label="Evaluations" />
                <NavLink href="/audit" label="Audit" />
                <NavLink href="/settings" label="Settings" />
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
