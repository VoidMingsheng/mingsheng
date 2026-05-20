import Link from "next/link";
import { ArrowUpRight, Eye, Filter, Search, UploadCloud } from "lucide-react";
import { MentorPanel } from "@/components/MentorPanel";
import { RubricTable } from "@/components/RubricTable";
import { ScoreGauge } from "@/components/ScoreGauge";
import { candidates, scoreAverages } from "@/lib/mockData";

const activeCandidate = candidates[0];

export default function DashboardPage() {
  return (
    <div className="page-stack">
      <header className="topbar">
        <div>
          <p className="eyebrow">Recruitment Review</p>
          <h1>Candidate intelligence dashboard</h1>
        </div>
        <div className="topbar-actions">
          <button className="icon-button" aria-label="Search candidates" title="Search candidates"><Search size={18} /></button>
          <button className="icon-button" aria-label="Filter candidates" title="Filter candidates"><Filter size={18} /></button>
          <Link className="primary-button" href="/candidates/new"><UploadCloud size={18} />New review</Link>
        </div>
      </header>

      <section className="metric-grid" aria-label="Pipeline metrics">
        <div className="metric"><span>Avg score</span><strong>{scoreAverages.total}</strong><small>Current slate</small></div>
        <div className="metric"><span>Technical avg</span><strong>{scoreAverages.technical}</strong><small>Out of 25</small></div>
        <div className="metric"><span>Communication avg</span><strong>{scoreAverages.communication}</strong><small>Out of 15</small></div>
        <div className="metric"><span>Critical pass</span><strong>{scoreAverages.criticalPassRate}%</strong><small>Minimum checks</small></div>
      </section>

      <div className="dashboard-grid">
        <section className="panel candidate-panel">
          <div className="panel-heading"><div><p className="eyebrow">Ranking Board</p><h2>Active candidates</h2></div><span className="status-pill">3 open</span></div>
          <div className="candidate-list">
            {candidates.map((candidate) => (
              <Link className="candidate-row" href={`/candidates/${candidate.id}`} key={candidate.id}>
                <div><strong>{candidate.name}</strong><span>{candidate.role}</span></div>
                <span className={`recommendation recommendation-${candidate.recommendation.toLowerCase().replace(" ", "-")}`}>{candidate.recommendation}</span>
                <ScoreGauge score={candidate.totalScore} label="Score" size="sm" />
                <span className={candidate.criticalPassed ? "check-pass" : "check-fail"}>{candidate.criticalPassed ? "Passed" : "Review"}</span>
                <ArrowUpRight size={16} />
              </Link>
            ))}
          </div>
        </section>

        <section className="panel result-panel">
          <div className="panel-heading"><div><p className="eyebrow">Current Result</p><h2>{activeCandidate.name}</h2></div><Link className="icon-button" aria-label="View candidate" title="View candidate" href={`/candidates/${activeCandidate.id}`}><Eye size={18} /></Link></div>
          <div className="result-summary"><ScoreGauge score={activeCandidate.totalScore} label={activeCandidate.recommendation} /><div className="summary-list"><span>{activeCandidate.department}</span><strong>{activeCandidate.role}</strong><small>Updated {activeCandidate.updatedAt}</small></div></div>
          <RubricTable scores={activeCandidate.categoryScores} />
        </section>

        <section className="panel">
          <div className="panel-heading"><div><p className="eyebrow">Evidence</p><h2>Strengths and gaps</h2></div></div>
          <div className="evidence-columns">
            <div><h3>Strengths</h3><ul>{activeCandidate.strengths.map((item) => <li key={item}>{item}</li>)}</ul></div>
            <div><h3>Weaknesses</h3><ul>{activeCandidate.weaknesses.map((item) => <li key={item}>{item}</li>)}</ul></div>
          </div>
          <div className="gap-strip">{activeCandidate.gaps.map((gap) => <span key={gap}>{gap}</span>)}</div>
        </section>

        <MentorPanel mentor={activeCandidate.mentor} />
      </div>

      <section className="compliance-band" id="compliance"><strong>Human review required</strong><span>Scores support recruiter judgment and must not be used as fully autonomous hiring decisions.</span></section>
    </div>
  );
}
