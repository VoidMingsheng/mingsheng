import type { CategoryScore } from "@/lib/types";

type RubricTableProps = {
  scores: CategoryScore[];
};

export function RubricTable({ scores }: RubricTableProps) {
  return (
    <div className="rubric-table" role="table" aria-label="Scoring rubric">
      <div className="rubric-row rubric-head" role="row">
        <span>Category</span>
        <span>Score</span>
        <span>Weight</span>
      </div>
      {scores.map((item) => {
        const percent = Math.round((item.score / item.maxScore) * 100);
        return (
          <div className="rubric-row" role="row" key={item.key}>
            <span>{item.label}</span>
            <strong>{item.score}</strong>
            <span className="meter" aria-label={`${percent}%`}>
              <span style={{ width: `${percent}%` }} />
            </span>
          </div>
        );
      })}
    </div>
  );
}
