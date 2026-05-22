"use client";

import { FormEvent, useState } from "react";
import { FileAudio, FileText, SendHorizontal } from "lucide-react";

const jobOptions = ["Software Engineer", "Project Manager", "Sales Consultant", "HR Executive"];
const mbtiOptions = ["Unknown", "INTJ", "INTP", "ENTJ", "ENFJ", "ESFJ", "ESTJ", "ENTP", "ESFP", "INFJ"];

export function CandidateUploadForm() {
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div className="field-grid">
        <label>
          Candidate name
          <input name="name" placeholder="Aisha Tan" required />
        </label>
        <label>
          Email
          <input name="email" type="email" placeholder="candidate@example.com" />
        </label>
        <label>
          Job position
          <select name="job" defaultValue={jobOptions[0]}>
            {jobOptions.map((job) => (
              <option key={job}>{job}</option>
            ))}
          </select>
        </label>
        <label>
          MBTI
          <select name="mbti" defaultValue="Unknown">
            {mbtiOptions.map((mbti) => (
              <option key={mbti}>{mbti}</option>
            ))}
          </select>
        </label>
      </div>

      <div className="upload-dropzone-grid">
        <label className="dropzone">
          <FileText size={24} />
          <span>Resume document</span>
          <input name="resume" type="file" accept=".pdf,.doc,.docx,.txt" />
        </label>
        <label className="dropzone">
          <FileAudio size={24} />
          <span>Interview recording</span>
          <input name="audio" type="file" accept="audio/*,video/*" />
        </label>
        <label className="dropzone">
          <FileText size={24} />
          <span>Transcript document</span>
          <input name="transcriptFile" type="file" accept=".txt,.vtt,.srt,.pdf,.doc,.docx" />
        </label>
      </div>

      <label>
        Interview transcript
        <textarea
          name="transcript"
          rows={8}
          placeholder="Paste transcript text, or import a transcript document above while recording transcription is being integrated."
          required
        />
      </label>

      <div className="form-actions">
        {submitted ? <span className="status-pill success">Queued for analysis</span> : null}
        <button className="primary-button" type="submit">
          <SendHorizontal size={18} />
          Run analysis
        </button>
      </div>
    </form>
  );
}
