import type { Candidate } from "./types";

export const candidates: Candidate[] = [
  {
    id: "cand-001",
    name: "Aisha Tan",
    role: "Software Engineer",
    department: "Software Engineering",
    status: "Review Ready",
    recommendation: "Hire",
    totalScore: 82,
    criticalPassed: true,
    updatedAt: "2026-05-20 18:35",
    categoryScores: [
      { key: "technical", label: "Technical", score: 20, maxScore: 25 },
      { key: "experience", label: "Experience", score: 13, maxScore: 15 },
      { key: "communication", label: "Communication", score: 12, maxScore: 15 },
      { key: "problem", label: "Problem Solving", score: 9, maxScore: 10 },
      { key: "culture", label: "Culture", score: 8, maxScore: 10 },
      { key: "personality", label: "Personality", score: 7, maxScore: 10 },
      { key: "learning", label: "Learning", score: 5, maxScore: 5 },
      { key: "confidence", label: "Confidence", score: 4, maxScore: 5 },
      { key: "leadership", label: "Leadership", score: 4, maxScore: 5 }
    ],
    strengths: ["Strong backend API examples", "Clear problem-solving structure", "Good job skill alignment"],
    weaknesses: ["Needs deeper cloud deployment evidence"],
    gaps: ["kubernetes", "observability"],
    coworkers: [
      { name: "Grace Lee", department: "Software Engineering", mbti: "INTJ", compatibilityScore: 91, availability: 72 },
      { name: "Daniel Chua", department: "Software Engineering", mbti: "ENTP", compatibilityScore: 84, availability: 58 },
      { name: "Mei Wong", department: "Project Management", mbti: "ENTJ", compatibilityScore: 67, availability: 81 }
    ]
  },
  {
    id: "cand-002",
    name: "Ravi Menon",
    role: "Project Manager",
    department: "Project Management",
    status: "Human Review",
    recommendation: "Consider",
    totalScore: 71,
    criticalPassed: true,
    updatedAt: "2026-05-20 17:10",
    categoryScores: [
      { key: "technical", label: "Technical", score: 16, maxScore: 25 },
      { key: "experience", label: "Experience", score: 12, maxScore: 15 },
      { key: "communication", label: "Communication", score: 13, maxScore: 15 },
      { key: "problem", label: "Problem Solving", score: 7, maxScore: 10 },
      { key: "culture", label: "Culture", score: 8, maxScore: 10 },
      { key: "personality", label: "Personality", score: 6, maxScore: 10 },
      { key: "learning", label: "Learning", score: 3, maxScore: 5 },
      { key: "confidence", label: "Confidence", score: 3, maxScore: 5 },
      { key: "leadership", label: "Leadership", score: 3, maxScore: 5 }
    ],
    strengths: ["Strong stakeholder communication", "Relevant delivery background"],
    weaknesses: ["Limited evidence for risk control depth"],
    gaps: ["budget ownership", "executive reporting"],
    coworkers: []
  },
  {
    id: "cand-003",
    name: "Lina Ho",
    role: "Sales Consultant",
    department: "Sales",
    status: "Analyzing",
    recommendation: "Weak Fit",
    totalScore: 58,
    criticalPassed: false,
    updatedAt: "2026-05-20 16:42",
    categoryScores: [
      { key: "technical", label: "Technical", score: 12, maxScore: 25 },
      { key: "experience", label: "Experience", score: 8, maxScore: 15 },
      { key: "communication", label: "Communication", score: 9, maxScore: 15 },
      { key: "problem", label: "Problem Solving", score: 6, maxScore: 10 },
      { key: "culture", label: "Culture", score: 7, maxScore: 10 },
      { key: "personality", label: "Personality", score: 6, maxScore: 10 },
      { key: "learning", label: "Learning", score: 4, maxScore: 5 },
      { key: "confidence", label: "Confidence", score: 3, maxScore: 5 },
      { key: "leadership", label: "Leadership", score: 3, maxScore: 5 }
    ],
    strengths: ["Good learning attitude", "Positive customer orientation"],
    weaknesses: ["Technical minimum not met", "Needs stronger sales methodology evidence"],
    gaps: ["crm", "negotiation", "pipeline forecasting"],
    coworkers: []
  }
];

export const scoreAverages = {
  total: 70,
  technical: 16,
  communication: 11,
  criticalPassRate: 67
};
