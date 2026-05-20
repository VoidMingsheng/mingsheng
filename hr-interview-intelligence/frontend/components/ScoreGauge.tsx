import type { CSSProperties } from "react";

type ScoreGaugeProps = {
  score: number;
  label: string;
  size?: "sm" | "lg";
};

export function ScoreGauge({ score, label, size = "lg" }: ScoreGaugeProps) {
  const normalized = Math.max(0, Math.min(score, 100));

  return (
    <div className={`score-gauge score-gauge-${size}`} aria-label={`${label}: ${normalized} out of 100`}>
      <div className="score-ring" style={{ "--score": `${normalized}%` } as CSSProperties}>
        <span>{normalized}</span>
      </div>
      <small>{label}</small>
    </div>
  );
}
