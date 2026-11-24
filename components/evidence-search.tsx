"use client";

import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const responseSchema = z.object({
  query: z.string(),
  method: z.literal("lexical_baseline"),
  status: z.enum(["matches_found", "no_evidence"]),
  note: z.string(),
  results: z.array(
    z.object({
      id: z.string(),
      section: z.string(),
      text: z.string(),
      source: z.string(),
      version: z.string(),
      start_line: z.number().int().positive(),
      end_line: z.number().int().positive(),
      document_sha256: z.string().regex(/^[a-f0-9]{64}$/),
      score: z.number(),
    }),
  ),
});
type Evidence = z.infer<typeof responseSchema>;
export type EvidencePassage = Evidence["results"][number];

export function EvidenceSearch({
  onRetrieved,
  onReview,
}: {
  onRetrieved: (message: string) => void;
  onReview?: (passage: EvidencePassage) => void;
}) {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<Evidence | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [local, setLocal] = useState(false);
  const request = useRef<AbortController | null>(null);
  useEffect(() => {
    setLocal(["localhost", "127.0.0.1"].includes(window.location.hostname));
    return () => request.current?.abort();
  }, []);

  async function search(event: React.FormEvent) {
    event.preventDefault();
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const timer = setTimeout(() => controller.abort(), 10000);
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch("/qa-api/retrieve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), limit: 3 }),
        signal: controller.signal,
      });
      if (!response.ok)
        throw new Error(
          response.status === 503
            ? "The requirements document is unavailable. Check the Python service configuration."
            : "The Python retrieval service could not complete the request. Check that it is running and retry.",
        );
      const evidence = responseSchema.parse(await response.json());
      if (controller.signal.aborted) return;
      setResult(evidence);
      onRetrieved(`Python retrieved ${evidence.results.length} passage(s) for “${evidence.query}”`);
    } catch (cause) {
      if (request.current !== controller) return;
      setError(
        controller.signal.aborted
          ? "The request timed out. Check the Python service and retry."
          : cause instanceof Error && !(cause instanceof z.ZodError)
            ? cause.message
            : "The service returned an unexpected response. No evidence was displayed.",
      );
    } finally {
      clearTimeout(timer);
      if (request.current === controller) setLoading(false);
    }
  }

  return (
    <section aria-label="Live Python evidence search">
      <p className="panel-description">
        Search the actual requirements through Python. Results include original text, source lines, and
        document version. This is keyword retrieval; no LLM is called.
      </p>
      {!local && (
        <div className="callout">
          <strong>Available in the local demo</strong>
          <p>The hosted Python service is not connected yet. Open the local project to run this search.</p>
        </div>
      )}
      <form onSubmit={search}>
        <label htmlFor="evidence-query">Requirement ID or search phrase</label>
        <div className="action-row" style={{ marginTop: 0 }}>
          <Input
            id="evidence-query"
            value={query}
            maxLength={2000}
            disabled={loading || !local}
            onChange={(e) => {
              setQuery(e.target.value);
              setResult(null);
              setError("");
            }}
            placeholder="Enter a requirement ID or phrase"
            style={{ flex: 1, minWidth: 160 }}
          />
          <Button disabled={loading || !query.trim() || !local} type="submit">
            {loading ? "Searching…" : "Find evidence"}
          </Button>
        </div>
      </form>
      {error && (
        <div role="alert" className="callout">
          {error}
        </div>
      )}
      <div role="status" aria-live="polite">
        {result && (
          <p className="scope-note">
            {result.results.length
              ? `${result.results.length} source passages found`
              : "No matching evidence found. Try another requirement ID or phrase."}
          </p>
        )}
      </div>
      {result?.results.map((p) => (
        <article className="evidence-card" key={`${p.document_sha256}-${p.id}`} style={{ marginTop: 20 }}>
          <span className="source-tag">
            {p.source} · {p.id} · lines {p.start_line}–{p.end_line} · v{p.version}
          </span>
          <h4 style={{ marginBottom: 10 }}>{p.section}</h4>
          <blockquote style={{ whiteSpace: "pre-wrap" }}>{p.text}</blockquote>
          <details className="scope-note">
            <summary>Inspect source fingerprint</summary>
            <code style={{ overflowWrap: "anywhere" }}>{p.document_sha256}</code>
          </details>
          {onReview && /^(?:[A-Z]+|section)-[0-9]+$/.test(p.id) && (
            <Button type="button" variant="outline" onClick={() => onReview(p)}>
              Review this evidence
            </Button>
          )}
        </article>
      ))}
      {result && <p className="scope-note">{result.note}</p>}
    </section>
  );
}
