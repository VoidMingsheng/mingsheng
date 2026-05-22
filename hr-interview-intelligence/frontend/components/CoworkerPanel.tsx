import { UsersRound } from "lucide-react";
import type { CoworkerMatch } from "@/lib/types";

type CoworkerPanelProps = {
  coworkers: CoworkerMatch[];
};

export function CoworkerPanel({ coworkers }: CoworkerPanelProps) {
  return (
    <section className="panel" id="coworkers">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Co-worker Matches</p>
          <h2>{coworkers.length ? "Recommended co-workers" : "Blank until hire recommendation"}</h2>
        </div>
        <UsersRound size={22} />
      </div>

      {coworkers.length ? (
        <div className="coworker-match-list">
          {coworkers.map((coworker) => (
            <article className="coworker-card" key={`${coworker.name}-${coworker.department}`}>
              <header>
                <strong>{coworker.name}</strong>
                <span className="status-pill success">{coworker.compatibilityScore}%</span>
              </header>
              <dl>
                <div>
                  <dt>Department</dt>
                  <dd>{coworker.department}</dd>
                </div>
                <div>
                  <dt>Personality</dt>
                  <dd>{coworker.mbti}</dd>
                </div>
                <div>
                  <dt>Availability</dt>
                  <dd>{coworker.availability}%</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      ) : (
        <p className="muted-panel">No co-worker match is shown because this candidate is not currently recommended to hire.</p>
      )}
    </section>
  );
}
