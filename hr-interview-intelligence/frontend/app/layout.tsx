import type { Metadata } from "next";
import Link from "next/link";
import { BarChart3, ShieldCheck, UploadCloud, UsersRound } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "HR Interview Intelligence",
  description: "Recruitment decision support dashboard"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="sidebar" aria-label="Primary navigation">
            <Link className="brand" href="/">
              <span className="brand-mark">HI</span>
              <span>
                <strong>HR Intel</strong>
                <small>Decision Support</small>
              </span>
            </Link>
            <nav className="nav-list">
              <Link href="/" className="nav-item"><BarChart3 size={18} />Dashboard</Link>
              <Link href="/candidates/new" className="nav-item"><UploadCloud size={18} />New Review</Link>
              <a href="#mentors" className="nav-item"><UsersRound size={18} />Mentors</a>
              <a href="#compliance" className="nav-item"><ShieldCheck size={18} />Compliance</a>
            </nav>
          </aside>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
