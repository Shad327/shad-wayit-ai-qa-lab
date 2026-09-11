"use client";
import { useEffect, useState } from "react";
import { z } from "zod";
const schema = z.object({mode: z.literal("actual_pytest_reports"), reports: z.array(z.object({
  file: z.string(), timestamp: z.string(), tests: z.array(z.object({name: z.string(), status: z.enum(["passed", "failed", "skipped"])})),
}))});
export function BrowserResults() {
  const [result, setResult] = useState<z.infer<typeof schema> | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    fetch("/qa-api/browser-results", {signal: controller.signal})
      .then(r => {if (!r.ok) throw Error(); return r.json();})
      .then(data => setResult(schema.parse(data)))
      .catch(() => setError("Results are unavailable. Start the local Python service and reopen this step."))
      .finally(() => clearTimeout(timer));
    return () => {clearTimeout(timer); controller.abort();};
  }, []);
  return <section aria-label="Actual browser test reports">
    <p className="panel-description">Actual pytest + Chromium runs, newest first. Tests are written by us, not generated from your scenario edits. This screen reads saved reports; it does not start tests.</p>
    {error && <p role="alert">{error}</p>}
    {!result && !error && <p role="status">Loading reports…</p>}
    {result?.reports.length === 0 && <p>No browser reports saved yet.</p>}
    {result?.reports.map(report => <article className="evidence-card" key={report.file} style={{marginBottom:16}}>
      <h4>{report.tests.filter(t=>t.status === "passed").length} passed · {report.tests.filter(t=>t.status === "failed").length} failed · {report.tests.filter(t=>t.status === "skipped").length} skipped</h4>
      <p className="scope-note">{report.timestamp} · {report.file}</p>
      <ul>{report.tests.map((test,i)=><li key={i} style={{overflowWrap:"anywhere"}}><strong>{test.status.toUpperCase()}</strong> — {test.name}</li>)}</ul>
    </article>)}
    <p className="scope-note">Scope: portfolio review persistence and NoiseLabz desktop Features navigation only. These checks do not establish full accessibility, wallet behavior, or complete AUTH-04 coverage. Screenshots and traces are saved locally with the run artifacts.</p>
  </section>;
}
