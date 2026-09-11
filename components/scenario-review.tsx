"use client";
import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const schema = z.object({ review: z.object({
  id: z.string(), scenario: z.string(), revision: z.number().int(), approved: z.boolean(),
  approved_at: z.string().nullable(), updated_at: z.string(), mode: z.literal("demo_data"),
}).nullable() });
type Review = NonNullable<z.infer<typeof schema>["review"]>;

export function ScenarioReview({ identifier, initial, onState, onContinue }: {
  identifier: string; initial: string;
  onState: (text: string, approved: boolean) => void; onContinue: () => void;
}) {
  const [text, setText] = useState(initial), [saved, setSaved] = useState<Review | null>(null);
  const [busy, setBusy] = useState(true), [ready, setReady] = useState(false), [error, setError] = useState("");
  const callback = useRef(onState); callback.current = onState;
  const dirty = !saved || text !== saved.scenario;
  async function request(method = "GET", approve = false) {
    setBusy(true); setError("");
    try {
      const response = await fetch(`/qa-api/reviews/${identifier}${approve ? "/approve" : ""}`, {
        method, headers: { "Content-Type": "application/json" }, signal: AbortSignal.timeout(10000),
        ...(method !== "GET" ? { body: JSON.stringify({ revision: saved?.revision ?? 0, ...(!approve ? { scenario: text } : {}) }) } : {}),
      });
      if (!response.ok) throw Error(response.status === 409
        ? "Another tab changed this review. Copy your unsaved text, then reload the saved review."
        : "Could not access saved reviews. Check that Python is running and try again. Your text is still here.");
      const { review } = schema.parse(await response.json());
      setSaved(review); setReady(true);
      if (review) setText(review.scenario);
      callback.current(review?.scenario ?? text, review?.approved ?? false);
    } catch (e) { setError(e instanceof z.ZodError ? "Unexpected service response. No save was confirmed." : e instanceof Error ? e.message : "Request failed."); }
    finally { setBusy(false); }
  }
  useEffect(() => {
    if (!["localhost", "127.0.0.1"].includes(window.location.hostname)) {
      setBusy(false); setError("Saved reviews are available in the local demo. The hosted Python service is not connected yet."); return;
    }
    const controller = new AbortController();
    callback.current(initial, false);
    fetch(`/qa-api/reviews/${identifier}`, { signal: controller.signal })
      .then(r => { if (!r.ok) throw Error(); return r.json(); })
      .then(body => { const {review} = schema.parse(body); setSaved(review); setReady(true); if (review) {setText(review.scenario); callback.current(review.scenario, review.approved);} })
      .catch(() => { if (!controller.signal.aborted) setError("Start the Python service, then reload the saved review."); })
      .finally(() => { if (!controller.signal.aborted) setBusy(false); });
    return () => controller.abort();
  }, [identifier, initial]);
  return <section aria-label="Saved scenario review">
    <p className="panel-description">Demo data · written example, not AI-generated. Edit, save, then approve the saved version.</p>
    <label htmlFor="saved-scenario">Scenario</label>
    <Textarea id="saved-scenario" value={text} maxLength={8000} disabled={busy || !ready}
      onChange={e => { setText(e.target.value); callback.current(e.target.value, false); }} />
    <p role="status" className="scope-note">{!ready ? "Saved state not loaded" : dirty ? "Unsaved changes · save before approving" : saved?.approved ? `Version ${saved.revision} approved · ${new Date(saved.approved_at!).toLocaleString()}` : `Version ${saved?.revision} saved · awaiting review`}</p>
    {error && <p role="alert" className="callout">{error}</p>}
    <div className="action-row">
      <Button disabled={busy || !ready || !dirty || !text.trim()} onClick={() => request("PUT")}>Save changes</Button>
      <Button disabled={busy || !ready || dirty || saved?.approved} onClick={() => request("POST", true)}>Approve saved version</Button>
      <Button variant="outline" disabled={busy || dirty || !saved?.approved} onClick={onContinue}>View template</Button>
    </div>
    <Button variant="ghost" disabled={busy} onClick={() => request()}>Reload saved review (replaces unsaved text)</Button>
    <p className="scope-note">Saved locally by Python. Changes clear approval when saved. Approval records a local action; reviewer identity is not verified. Templates are still prepared examples, not generated from your edits.</p>
  </section>;
}
