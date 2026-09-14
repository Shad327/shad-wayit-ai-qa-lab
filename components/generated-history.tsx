"use client";
import {useEffect,useState} from "react";
import {z} from "zod";
import {Button} from "@/components/ui/button";
import {GeneratedEvidence} from "@/components/generated-evidence";
const schema=z.object({runs:z.array(z.object({id:z.string().uuid(),state:z.enum(["queued","running","passed","failed","error","timed_out","interrupted"]),approved_at:z.string(),finished_at:z.string().nullable(),report:z.string().nullable(),plan_hash:z.string()}))});
export function GeneratedHistory(){
 const [runs,setRuns]=useState<z.infer<typeof schema>["runs"]>([]),[selected,setSelected]=useState<string|null>(null),[refresh,setRefresh]=useState(0),[busy,setBusy]=useState(true),[error,setError]=useState("");
 useEffect(()=>{let mounted=true;setBusy(true);setError("");
 fetch('/qa-api/generated-runs',{signal:AbortSignal.timeout(10000)}).then(async r=>{if(!r.ok)throw Error();return schema.parse(await r.json());}).then(body=>{if(mounted){setRuns(body.runs);setSelected(current=>body.runs.some(r=>r.id===current)?current:null);}}).catch(()=>{if(mounted)setError('Generated run history is unavailable. Start Python and refresh.');}).finally(()=>{if(mounted)setBusy(false);});return()=>{mounted=false;};},[refresh]);
 const run=runs.find(r=>r.id===selected);
 return <section className="callout" aria-label="Generated test history"><h3>Generated test runs</h3><p>Latest 10 local template-generated runs, newest first. These are separate from the hand-written regression suite.</p><Button disabled={busy} variant="outline" onClick={()=>setRefresh(n=>n+1)}>Refresh generated history</Button>
 {busy&&<p role="status">Loading generated history…</p>}{error&&<p role="alert">{error}</p>}{!busy&&!error&&!runs.length&&<p>No generated runs yet. Approve and run the supported guest test from Review.</p>}
 {runs.map(r=><div key={r.id} className="history-entry"><Button variant="ghost" aria-pressed={selected===r.id} onClick={()=>setSelected(r.id)}>{r.state} · {new Date(r.approved_at).toLocaleString()}</Button><p className="scope-note">Run {r.id}</p></div>)}
 {run&&<article aria-label="Selected generated run"><p>Status: <strong>{run.state}</strong></p><p className="scope-note">Approved plan: {run.plan_hash}</p>{run.report&&<a href={`/qa-api/generated-runs/${run.id}/report`}>Download this run’s report</a>}{run.finished_at?<GeneratedEvidence key={run.id} runId={run.id}/>:<p>Run is active. Refresh history to check completion.</p>}</article>}
 </section>;
}
