"use client";
import { useEffect, useState } from "react";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { RunSuite } from "@/components/run-suite";
const schema = z.object({mode: z.literal("actual_pytest_reports"), reports: z.array(z.object({
  file: z.string(), timestamp: z.string(), tests: z.array(z.object({
    name: z.string(), status: z.enum(["passed", "failed", "skipped"]),
    case_id: z.string().nullable(), title: z.string(), screenshot: z.string().nullable(),
  })),
}))});
export function BrowserResults() {
  const [result, setResult] = useState<z.infer<typeof schema> | null>(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0), [busy, setBusy] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    let active = true;
    setBusy(true); setError("");
    fetch("/qa-api/browser-results", {signal: controller.signal})
      .then(r => {if (!r.ok) throw Error(); return r.json();})
      .then(data => {if (active) setResult(schema.parse(data));})
      .catch(() => {if (active) setError("Results are unavailable. Start the local Python service, then refresh results.");})
      .finally(() => {clearTimeout(timer); if (active) setBusy(false);});
    return () => {active = false; clearTimeout(timer); controller.abort();};
  }, [refresh]);
  const latest = result?.reports.find(r => r.tests.some(t => t.case_id));
  const cases = latest?.tests.filter(t => t.case_id) ?? [];
  const keyboard = cases.find(t => t.case_id === "KEY-02");
  return <section aria-label="NoiseLabz quality demo">
    <p className="eyebrow">NOISELABZ / PUBLIC UI REGRESSION</p>
    <p className="panel-description">Real Chromium runs against the public website. Each check has a case ID, a result, and captured evidence.</p>
    <RunSuite onComplete={()=>setRefresh(v=>v+1)}/>
    <Button variant="outline" disabled={busy} onClick={() => setRefresh(v => v + 1)}>{busy ? "Loading…" : "Refresh results"}</Button>
    {error && <p role="alert" className="callout">{error} {result && "Previously loaded results remain below."}</p>}
    {latest && <>
      <div className="run-summary" aria-label="Latest NoiseLabz run">
        <div><strong>{cases.length}</strong><span>checks executed</span></div>
        <div><strong>{cases.filter(t=>t.status === "passed").length}</strong><span>passed</span></div>
        <div><strong className="failure-text">{cases.filter(t=>t.status === "failed").length}</strong><span>failed</span></div>
      </div>
      <p className="scope-note">Recorded {new Date(latest.timestamp).toLocaleString()} · Chromium · desktop and 390 × 844 mobile viewport</p>
      <div className="test-case-list">{cases.map(test => <details key={test.name} className="test-case">
        <summary><span className="case-id">{test.case_id}</span><span>{test.title}</span><strong className={`test-status ${test.status}`}>{test.status}</strong></summary>
        <p className="scope-note">Python test: <code>{test.name}</code></p>
        {test.screenshot ? <figure><a href={test.screenshot} target="_blank" rel="noreferrer"><img src={test.screenshot} alt={`${test.case_id}: browser captured at end of ${test.status} test`} loading="lazy" /></a><figcaption>Actual run capture. Click to view full size. Assertions establish keyboard behavior; this screenshot alone does not.</figcaption></figure> : <p>No screenshot associated with this report.</p>}
      </details>)}</div>
      {keyboard?.status === "failed" && <article className="finding-card" aria-label="Keyboard accessibility finding">
        <p className="eyebrow">FINDING / NOISE-UI-001 · KEY-02</p>
        <h4>Visible menu. Missing keyboard access.</h4>
        <p>The mobile menu trigger did not receive focus during 20 Tab presses. The separate click test checks pointer access.</p>
        <dl><dt>Reproduce</dt><dd>Open NoiseLabz in a fresh browser at 390 × 844. Press Tab to navigate toward the menu icon.</dd><dt>Expected</dt><dd>The menu trigger receives keyboard focus and can be activated.</dd><dt>Investigate</dt><dd>The inspected trigger was a clickable div. Use a named native button and verify focus, Enter/Space activation, and menu state.</dd></dl>
        <p className="scope-note">Normal-priority recommendation, subject to product triage. No fix has been applied to NoiseLabz. Review the assertion if the site or test changes.</p>
      </article>}
    </>}
    {!busy && !error && !latest && <p>No NoiseLabz report yet. Run the suite below to create one.</p>}
    <details className="demo-guide"><summary>How to demonstrate this project</summary>
      <ol><li>Explain the scope: public navigation and keyboard access, without signing in.</li><li>Expand KEY-02 and inspect the screenshot and Python test name.</li><li>Explain the failure, its impact, and the proposed fix.</li><li>Rerun the suite, then refresh results to show fresh evidence.</li></ol>
      <p>From a terminal in the project folder:</p><pre><code>.venv/bin/python -m qa_pipeline.run_noiselabz --headed</code></pre>
      <p className="scope-note">Each run saves a new report, screenshots, and traces. Failed tests return a failure exit code.</p>
    </details>
    <details className="demo-guide"><summary>Recent run history</summary>{result?.reports.map(report => <div className="history-entry" key={report.file}>
      <strong>{report.tests.filter(t=>t.status === "passed").length} passed · {report.tests.filter(t=>t.status === "failed").length} failed · {report.tests.filter(t=>t.status === "skipped").length} skipped</strong>
      <p className="scope-note">{report.timestamp} · {report.file}</p>
    </div>)}</details>
    <p className="scope-note">Working today: hand-written Playwright tests, report parsing, and evidence display. AI generation is not connected. This is narrow landing-page coverage, not complete product or accessibility certification.</p>
  </section>;
}
