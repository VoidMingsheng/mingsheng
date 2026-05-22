const jobs = [
  {
    id: "software-engineer",
    title: "Software Engineer",
    department: "Software Engineering",
    skills: ["python", "fastapi", "postgresql", "system design", "testing"],
    preferredMbti: ["INTJ", "INTP"]
  },
  {
    id: "project-manager",
    title: "Project Manager",
    department: "Project Management",
    skills: ["stakeholder management", "planning", "risk management", "agile", "communication"],
    preferredMbti: ["ENTJ", "ESTJ"]
  },
  {
    id: "sales-consultant",
    title: "Sales Consultant",
    department: "Sales",
    skills: ["sales", "crm", "negotiation", "presentation", "relationship management"],
    preferredMbti: ["ENTP", "ENFJ", "ESFP"]
  }
];

const coworkers = [
  { id: "emp-001", name: "Grace Lee", department: "Software Engineering", mbti: "INTJ", score: 4.8, availability: 72 },
  { id: "emp-002", name: "Daniel Chua", department: "Software Engineering", mbti: "ENTP", score: 4.4, availability: 58 },
  { id: "emp-003", name: "Mei Wong", department: "Project Management", mbti: "ENTJ", score: 4.7, availability: 81 },
  { id: "emp-004", name: "Irfan Rahman", department: "Sales", mbti: "ENFJ", score: 4.6, availability: 63 }
];

const seedCandidates = [
  createCandidate({
    name: "Aisha Tan",
    email: "aisha@example.com",
    jobId: "software-engineer",
    mbti: "INTJ",
    resume:
      "Python backend engineer with 5 years experience. Built FastAPI services using PostgreSQL, testing, Docker, and system design for scalable APIs.",
    transcript:
      "I designed an API architecture with FastAPI and PostgreSQL. I owned testing and deployment, debugged performance issues, and explained tradeoffs with security and scalability. I learned from feedback and coached junior engineers."
  }),
  createCandidate({
    name: "Ravi Menon",
    email: "ravi@example.com",
    jobId: "project-manager",
    mbti: "ENTJ",
    resume:
      "Project manager with 4 years experience in agile planning, stakeholder management, communication, and delivery tracking.",
    transcript:
      "I coordinated stakeholders, planned delivery risks, and improved team communication. I handled constraints by prioritizing scope and documenting risk management decisions."
  }),
  createCandidate({
    name: "Lina Ho",
    email: "lina@example.com",
    jobId: "sales-consultant",
    mbti: "ENFJ",
    resume:
      "Customer support specialist with 2 years experience. Interested in sales and relationship management.",
    transcript:
      "I enjoy customer conversations and learned quickly from feedback. I have presented to customers, but I am still building CRM, negotiation, and pipeline forecasting experience."
  })
];

let state = loadState();
let selectedId = state.selectedId || state.candidates[0]?.id;

function loadState() {
  const saved = localStorage.getItem("hr-demo-state");
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      parsed.candidates = (parsed.candidates || []).map((candidate) =>
        Array.isArray(candidate.coworkerMatches)
          ? candidate
          : createCandidate({
              ...candidate,
              jobId: candidate.jobId || jobs.find((job) => job.title === candidate.role)?.id || jobs[0].id,
              resume: candidate.resume || "Legacy demo resume text.",
              transcript: candidate.transcript || "Legacy demo transcript text."
            })
      );
      return parsed;
    } catch {
      localStorage.removeItem("hr-demo-state");
    }
  }
  return { candidates: seedCandidates, selectedId: seedCandidates[0].id };
}

function saveState() {
  localStorage.setItem("hr-demo-state", JSON.stringify({ candidates: state.candidates, selectedId }));
}

function words(text) {
  return (text.toLowerCase().match(/[a-z']+/g) || []);
}

function countHits(text, terms) {
  const lowered = text.toLowerCase();
  return terms.filter((term) => lowered.includes(term)).length;
}

function yearsExperience(text) {
  const matches = [...text.matchAll(/(\d+(?:\.\d+)?)\+?\s+years?/gi)].map((match) => Number(match[1]));
  return matches.length ? Math.max(...matches) : 0;
}

function clamp(value, max) {
  return Math.max(0, Math.min(Math.round(value), max));
}

function recommendation(total) {
  if (total >= 85) return "Strong Hire";
  if (total >= 75) return "Hire";
  if (total >= 65) return "Consider";
  if (total >= 50) return "Weak Fit";
  return "Reject";
}

function pillClass(label, criticalPassed = true) {
  if (!criticalPassed) return "rose";
  if (label === "Strong Hire" || label === "Hire") return "green";
  if (label === "Reject") return "rose";
  return "amber";
}

function coworkerCompatibility(candidateMbti, coworker, job) {
  let score = coworker.department === job.department ? 35 : 12;
  score += coworker.score * 4;
  score += coworker.availability * 0.2;
  if (candidateMbti !== "Unknown" && candidateMbti === coworker.mbti) score += 20;
  else if (job.preferredMbti.includes(coworker.mbti)) score += 12;
  else score += 6;
  return Math.round(score);
}

function rankedCoworkers(candidateMbti, job, limit = 4) {
  return coworkers
    .map((coworker) => ({ ...coworker, compatibility: coworkerCompatibility(candidateMbti, coworker, job) }))
    .sort((a, b) => b.compatibility - a.compatibility)
    .slice(0, limit);
}

function createCandidate(input) {
  const job = jobs.find((item) => item.id === input.jobId) || jobs[0];
  const combined = `${input.resume} ${input.transcript}`.toLowerCase();
  const transcriptWords = words(input.transcript);
  const fillerWords = ["um", "uh", "like", "basically", "actually"];
  const fillerCount = transcriptWords.filter((word) => fillerWords.includes(word)).length;
  const fillerRate = fillerCount / Math.max(transcriptWords.length, 1);
  const matchedSkills = job.skills.filter((skill) => combined.includes(skill));
  const gaps = job.skills.filter((skill) => !matchedSkills.includes(skill));
  const skillMatch = job.skills.length ? matchedSkills.length / job.skills.length : 1;
  const years = yearsExperience(input.resume);
  const technicalHits = countHits(input.transcript, ["architecture", "api", "database", "testing", "deployment", "security", "scalability", "debug", "design"]);
  const problemHits = countHits(input.transcript, ["tradeoff", "root cause", "hypothesis", "debug", "prioritize", "risk", "constraint"]);
  const leadershipHits = countHits(input.transcript, ["led", "owned", "coached", "coordinated", "initiated", "improved", "delivered"]);
  const learningHits = countHits(input.transcript, ["learned", "adapted", "curious", "feedback", "improved", "experimented"]);

  const technical = clamp(9 + technicalHits * 2.5 + skillMatch * 8, 25);
  const experience = clamp(Math.min(years / 5, 1) * 15 || 5, 15);
  const communication = clamp(12 - (fillerRate > 0.05 ? 3 : 0) - (transcriptWords.length < 55 ? 2 : 0), 15);
  const problem = clamp(4 + problemHits * 2, 10);
  const culture = 7;
  const personality = input.mbti !== "Unknown" && job.preferredMbti.includes(input.mbti) ? 9 : 6;
  const learning = clamp(2 + learningHits, 5);
  const confidence = fillerRate > 0.05 ? 3 : 4;
  const leadership = clamp(2 + leadershipHits, 5);

  const categoryScores = [
    ["technical", "Technical", technical, 25],
    ["experience", "Experience", experience, 15],
    ["communication", "Communication", communication, 15],
    ["problem", "Problem Solving", problem, 10],
    ["culture", "Culture", culture, 10],
    ["personality", "Personality", personality, 10],
    ["learning", "Learning", learning, 5],
    ["confidence", "Confidence", confidence, 5],
    ["leadership", "Leadership", leadership, 5]
  ].map(([key, label, score, max]) => ({ key, label, score, max }));

  const total = categoryScores.reduce((sum, item) => sum + item.score, 0);
  const criticalPassed = technical >= 15 && communication >= 8;
  let rec = recommendation(total);
  if (!criticalPassed && (rec === "Strong Hire" || rec === "Hire")) rec = "Consider";

  const strengths = [];
  if (skillMatch >= 0.75) strengths.push("Strong keyword alignment with the target job description.");
  if (technicalHits >= 3) strengths.push("Clear technical vocabulary and project explanation signals.");
  if (problemHits >= 2) strengths.push("Shows structured problem-solving evidence.");
  if (leadershipHits >= 2) strengths.push("Shows ownership or leadership examples.");
  if (!strengths.length) strengths.push("Baseline candidate profile captured for HR review.");

  const weaknesses = [];
  if (gaps.length) weaknesses.push(`Missing or weak evidence for: ${gaps.join(", ")}.`);
  if (fillerRate > 0.05) weaknesses.push("Communication may need coaching due to filler-heavy responses.");
  if (transcriptWords.length < 55) weaknesses.push("Transcript is short, so confidence in analysis is limited.");

  const coworkerMatches = criticalPassed && ["Strong Hire", "Hire"].includes(rec) ? rankedCoworkers(input.mbti, job) : [];

  return {
    id: input.id || `cand-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    name: input.name,
    email: input.email,
    role: job.title,
    department: job.department,
    jobId: job.id,
    mbti: input.mbti,
    resume: input.resume,
    transcript: input.transcript,
    recommendation: rec,
    totalScore: total,
    criticalPassed,
    updatedAt: new Date().toLocaleString(),
    categoryScores,
    strengths,
    weaknesses,
    gaps,
    coworkerMatches,
    metrics: {
      skillMatchPercent: Math.round(skillMatch * 100),
      yearsExperience: years,
      fillerRate: Math.round(fillerRate * 1000) / 10
    }
  };
}

function renderJobOptions() {
  const select = document.querySelector("#jobSelect");
  select.innerHTML = jobs.map((job) => `<option value="${job.id}">${job.title}</option>`).join("");
}

function renderMetrics() {
  const candidates = state.candidates;
  const avg = (items, fn) => Math.round(items.reduce((sum, item) => sum + fn(item), 0) / Math.max(items.length, 1));
  document.querySelector("#avgScore").textContent = avg(candidates, (item) => item.totalScore);
  document.querySelector("#technicalAvg").textContent = avg(candidates, (item) => item.categoryScores[0].score);
  document.querySelector("#communicationAvg").textContent = avg(candidates, (item) => item.categoryScores[2].score);
  document.querySelector("#criticalPass").textContent = `${avg(candidates, (item) => (item.criticalPassed ? 100 : 0))}%`;
  document.querySelector("#openCount").textContent = `${candidates.length} open`;
}

function renderCandidateList() {
  const list = document.querySelector("#candidateList");
  list.innerHTML = state.candidates
    .sort((a, b) => b.totalScore - a.totalScore)
    .map((candidate) => {
      const active = candidate.id === selectedId ? " active" : "";
      return `
        <button class="candidate-row${active}" data-candidate-id="${candidate.id}">
          <div><strong>${candidate.name}</strong><br><small>${candidate.role}</small></div>
          <span class="pill ${pillClass(candidate.recommendation, candidate.criticalPassed)}">${candidate.recommendation}</span>
          <div class="score-ring small" style="--score:${candidate.totalScore}%"><strong>${candidate.totalScore}</strong></div>
          <span class="pill ${candidate.criticalPassed ? "green" : "rose"}">${candidate.criticalPassed ? "Passed" : "Review"}</span>
        </button>
      `;
    })
    .join("");
}

function renderSelectedCandidate() {
  const candidate = state.candidates.find((item) => item.id === selectedId) || state.candidates[0];
  if (!candidate) return;
  selectedId = candidate.id;
  document.querySelector("#candidateName").textContent = candidate.name;
  document.querySelector("#totalScore").textContent = candidate.totalScore;
  document.querySelector("#scoreRing").style.setProperty("--score", `${candidate.totalScore}%`);
  document.querySelector("#recommendation").textContent = candidate.recommendation;
  document.querySelector("#department").textContent = candidate.department;
  document.querySelector("#role").textContent = candidate.role;
  document.querySelector("#updatedAt").textContent = `Updated ${candidate.updatedAt}`;
  const critical = document.querySelector("#criticalStatus");
  critical.textContent = candidate.criticalPassed ? "Critical minimums passed" : "Critical review required";
  critical.className = `pill ${candidate.criticalPassed ? "green" : "rose"}`;

  document.querySelector("#rubricTable").innerHTML = `
    <div class="rubric-row rubric-head"><span>Category</span><span>Score</span><span>Weight</span></div>
    ${candidate.categoryScores
      .map((item) => {
        const percent = Math.round((item.score / item.max) * 100);
        return `<div class="rubric-row"><span>${item.label}</span><strong>${item.score}</strong><span class="meter"><span style="width:${percent}%"></span></span></div>`;
      })
      .join("")}
  `;

  document.querySelector("#strengthsList").innerHTML = candidate.strengths.map((item) => `<li>${item}</li>`).join("");
  document.querySelector("#weaknessesList").innerHTML = candidate.weaknesses.map((item) => `<li>${item}</li>`).join("");
  document.querySelector("#gapStrip").innerHTML = candidate.gaps.length
    ? candidate.gaps.map((gap) => `<span>${gap}</span>`).join("")
    : "<span>No required skill gaps detected</span>";

  const matches = candidate.coworkerMatches || [];
  document.querySelector("#coworkerPanelTitle").textContent = matches.length ? "Recommended co-workers" : "Blank until hire recommendation";
  document.querySelector("#coworkerMatches").innerHTML = matches.length
    ? matches.map(renderCoworkerCard).join("")
    : `<div class="muted">No co-worker match is shown because this candidate is not currently recommended to hire.</div>`;
  document.querySelector("#coworkerNote").textContent = matches.length
    ? "Percentiles combine department, availability, onboarding score, and personality compatibility."
    : "Co-worker matching appears only for recommended hires.";
}

function renderCoworkerCard(coworker) {
  return `
    <article class="coworker-card">
      <header><strong>${coworker.name}</strong><span class="pill green">${coworker.compatibility}%</span></header>
      <dl>
        <div><dt>Department</dt><dd>${coworker.department}</dd></div>
        <div><dt>Personality</dt><dd>${coworker.mbti}</dd></div>
        <div><dt>Onboarding score</dt><dd>${coworker.score}/5</dd></div>
        <div><dt>Availability</dt><dd>${coworker.availability}%</dd></div>
      </dl>
    </article>
  `;
}

function renderCoworkerDirectory() {
  document.querySelector("#coworkerDirectory").innerHTML = coworkers
    .map((coworker) => renderCoworkerCard({ ...coworker, compatibility: coworker.availability }))
    .join("");
}

function render() {
  renderMetrics();
  renderCandidateList();
  renderSelectedCandidate();
  saveState();
}

function showSection(id) {
  document.querySelectorAll(".section").forEach((section) => section.classList.toggle("active", section.id === id));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.section === id));
}

function exportCandidate() {
  const candidate = state.candidates.find((item) => item.id === selectedId);
  if (!candidate) return;
  const blob = new Blob([JSON.stringify(candidate, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${candidate.name.toLowerCase().replaceAll(" ", "-")}-analysis.json`;
  link.click();
  URL.revokeObjectURL(url);
}

document.addEventListener("click", (event) => {
  const sectionButton = event.target.closest("[data-section]");
  if (sectionButton) showSection(sectionButton.dataset.section);

  const row = event.target.closest("[data-candidate-id]");
  if (row) {
    selectedId = row.dataset.candidateId;
    render();
  }
});

document.querySelector("#analysisForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const candidate = createCandidate({
    name: form.get("name"),
    email: form.get("email"),
    jobId: form.get("job"),
    mbti: form.get("mbti"),
    resume: form.get("resume"),
    transcript: form.get("transcript"),
    resumeDocumentName: document.querySelector("#resumeFile").files[0]?.name || "",
    recordingName: document.querySelector("#recordingFile").files[0]?.name || "",
    transcriptDocumentName: document.querySelector("#transcriptFile").files[0]?.name || ""
  });
  state.candidates = [candidate, ...state.candidates];
  selectedId = candidate.id;
  document.querySelector("#formStatus").textContent = "Analysis complete and added to dashboard.";
  event.currentTarget.reset();
  showSection("dashboard");
  render();
});

async function fillTextFromFile(inputId, textareaName, statusId) {
  const input = document.querySelector(inputId);
  const file = input.files[0];
  if (!file) return;
  const status = document.querySelector(statusId);
  status.textContent = `Selected: ${file.name}`;
  if (/\.(txt|vtt|srt)$/i.test(file.name)) {
    const text = await file.text();
    document.querySelector(`[name="${textareaName}"]`).value = text;
    status.textContent = `Imported text from ${file.name}`;
  }
}

document.querySelector("#resumeFile").addEventListener("change", () => fillTextFromFile("#resumeFile", "resume", "#resumeFileStatus"));
document.querySelector("#transcriptFile").addEventListener("change", () => fillTextFromFile("#transcriptFile", "transcript", "#transcriptFileStatus"));
document.querySelector("#recordingFile").addEventListener("change", () => {
  const file = document.querySelector("#recordingFile").files[0];
  document.querySelector("#recordingFileStatus").textContent = file
    ? `Selected: ${file.name}. Paste transcript text or connect backend transcription later.`
    : "Recording import is tracked; transcription is a backend feature.";
});

document.querySelector("#exportCandidate").addEventListener("click", exportCandidate);

document.querySelector("#resetDemo").addEventListener("click", () => {
  localStorage.removeItem("hr-demo-state");
  state = { candidates: seedCandidates, selectedId: seedCandidates[0].id };
  selectedId = state.selectedId;
  render();
});

renderJobOptions();
renderCoworkerDirectory();
render();
