export type CategoryScore = {
  key: string;
  label: string;
  score: number;
  maxScore: number;
};

export type CoworkerMatch = {
  name: string;
  department: string;
  mbti: string;
  compatibilityScore: number;
  availability: number;
};

export type Candidate = {
  id: string;
  name: string;
  role: string;
  department: string;
  status: "Review Ready" | "Human Review" | "Analyzing";
  recommendation: "Strong Hire" | "Hire" | "Consider" | "Weak Fit" | "Reject";
  totalScore: number;
  criticalPassed: boolean;
  updatedAt: string;
  categoryScores: CategoryScore[];
  strengths: string[];
  weaknesses: string[];
  gaps: string[];
  coworkers: CoworkerMatch[];
};
