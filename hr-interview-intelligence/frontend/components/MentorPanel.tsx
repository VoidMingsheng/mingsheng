import { CalendarClock, UserRoundCheck } from "lucide-react";
import type { MentorRecommendation } from "@/lib/types";

type MentorPanelProps = {
  mentor: MentorRecommendation;
};

export function MentorPanel({ mentor }: MentorPanelProps) {
  return (
    <section className="panel" id="mentors">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Mentor Match</p>
          <h2>{mentor.name}</h2>
        </div>
        <UserRoundCheck size={22} />
      </div>
      <dl className="mentor-grid">
        <div>
          <dt>Department</dt>
          <dd>{mentor.department}</dd>
        </div>
        <div>
          <dt>MBTI</dt>
          <dd>{mentor.mbti}</dd>
        </div>
        <div>
          <dt>Compatibility</dt>
          <dd>{mentor.compatibilityScore}%</dd>
        </div>
        <div>
          <dt>Availability</dt>
          <dd>{mentor.availability}%</dd>
        </div>
      </dl>
      <div className="mentor-note">
        <CalendarClock size={16} />
        <span>Used for onboarding support only.</span>
      </div>
    </section>
  );
}
