import Link from "next/link";
import { ArrowLeft, CheckCircle2, TriangleAlert } from "lucide-react";
import { CoworkerPanel } from "@/components/CoworkerPanel";
import { RubricTable } from "@/components/RubricTable";
import { ScoreGauge } from "@/components/ScoreGauge";
import { candidates } from "@/lib/mockData";

type CandidateDetailPageProps = {
  params: {
    id: string;
  };
};

export default function CandidateDetailPage({ params }: CandidateDetailPageProps) {
  const candidate = candidates.find((item) => item.id === params.id) ?? candidates[0];

  return (
    <div className="page-stack">
      <header className="topbar">
        <div>
          <p className="eyebrow">{candidate.status}</p>
          <h1>{candidate.name}</h1>
        </div>
        <Link className="secondary-button" href="/">
          <ArrowLeft size={18} />
          Dashboard
        </Link>
      </header>

      <div className="detail-grid">
        <section className="panel">
          <div className="result-summary">
            <ScoreGauge score={candidate.totalScore} label={candidate.recommendation} />
            <div className="summary-list">
              <span>{candidate.department}</span>
              <strong>{candidate.role}</strong>
              <small>Updated {candidate.updatedAt}</small>
              <span className={candidate.criticalPassed ? "check-pass inline-check" : "check-fail inline-check"}>
                {candidate.criticalPassed ? <CheckCircle2 size={16} /> : <TriangleAlert size={16} />}
                {candidate.criticalPassed ? "Critical minimums passed" : "Critical review required"}
              </span>
            </div>
          </div>
        </section>

        <CoworkerPanel coworkers={candidate.coworkers} />
      </div>

      <div className="dashboard-grid two-column">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Rubric</p>
              <h2>Score breakdown</h2>
            </div>
          </div>
          <RubricTable scores={candidate.categoryScores} />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Review Notes</p>
              <h2>Evidence summary</h2>
            </div>
          </div>
          <div className="evidence-columns single">
            <div>
              <h3>Strengths</h3>
              <ul>
                {candidate.strengths.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Weaknesses</h3>
              <ul>
                {candidate.weaknesses.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="gap-strip">
            {candidate.gaps.map((gap) => (
              <span key={gap}>{gap}</span>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
