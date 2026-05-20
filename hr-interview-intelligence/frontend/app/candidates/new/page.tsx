import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { CandidateUploadForm } from "@/components/CandidateUploadForm";

export default function NewCandidatePage() {
  return (
    <div className="page-stack narrow-page">
      <header className="topbar">
        <div><p className="eyebrow">New Review</p><h1>Candidate intake</h1></div>
        <Link className="secondary-button" href="/"><ArrowLeft size={18} />Dashboard</Link>
      </header>
      <section className="panel"><CandidateUploadForm /></section>
    </div>
  );
}
