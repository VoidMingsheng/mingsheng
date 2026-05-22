const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function analyzeCandidate<TPayload, TResult>(payload: TPayload): Promise<TResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/candidates/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Candidate analysis failed with status ${response.status}`);
  }

  return response.json() as Promise<TResult>;
}
