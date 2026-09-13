"use client";
import { useEffect, useRef, useState } from "react";
import { z } from "zod";
import { Button } from "@/components/ui/button";

const planSchema = z.object({hash:z.string(),case_ids:z.array(z.string()),target:z.string(),scope:z.string(),timeout_seconds:z.number()});
const runSchema = z.object({run:z.object({id:z.string(),state:z.enum(["queued","running","passed","failed","error","timed_out","interrupted"]),approved_at:z.string(),finished_at:z.string().nullable(),note:z.string().nullable()}).nullable()});
type Run = z.infer<typeof runSchema>["run"];
const active = (run:Run) => run?.state === "queued" || run?.state === "running";

export function RunSuite({onComplete}:{onComplete:()=>void}) {
  const [plan,setPlan]=useState<z.infer<typeof planSchema>|null>(null);
  const [run,setRun]=useState<Run>(null),[approved,setApproved]=useState(false);
  const [error,setError]=useState(""),[busy,setBusy]=useState(false),[reload,setReload]=useState(0);
  const completion=useRef(onComplete);completion.current=onComplete;
  const requestId=useRef<string|null>(null);
  const completed=useRef<string|null>(null);
  async function read(path:string,init?:RequestInit){
    const response=await fetch(`/qa-api${path}`,{...init,signal:AbortSignal.timeout(10000)});
    if(!response.ok){const body=z.object({detail:z.string()}).safeParse(await response.json().catch(()=>null));throw Error(body.success ? body.data.detail : "The local runner is unavailable.");}
    return response.json();
  }
  useEffect(()=>{
    let mounted=true;
    setError("");setApproved(false);setPlan(null);
    Promise.all([read("/runs/plan"),read("/runs/latest")]).then(([p,r])=>{if(mounted){setPlan(planSchema.parse(p));setRun(runSchema.parse(r).run);}})
      .catch(()=>{if(mounted)setError("Start the local Python service, then reload the run plan.");});
    return()=>{mounted=false;};
  },[reload]);
  useEffect(()=>{
    if(!active(run)) return;
    let mounted=true;
    const timer=setInterval(()=>{read(`/runs/${run!.id}`).then(body=>{
      if(!mounted)return;
      const next=runSchema.parse(body).run;setRun(next);setError("");
      if(next&&!active(next)&&completed.current!==next.id){completed.current=next.id;completion.current();}
    }).catch(()=>{if(mounted)setError("Status temporarily unavailable. Checking again; no extra run will be started.");});},2000);
    return()=>{mounted=false;clearInterval(timer);};
  },[run?.id,run?.state]);
  async function start(){
    if(!plan||!approved)return;
    setBusy(true);setError("");
    requestId.current ??= crypto.randomUUID();
    try{
      const body=await read("/runs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({request_id:requestId.current,plan_hash:plan.hash,approved:true})});
      const next=runSchema.parse(body).run;setRun(next);setApproved(false);requestId.current=null;
      if(next&&!active(next))completion.current();
    }catch(e){setError(e instanceof Error?e.message:"Run request failed. Retry uses the same request ID.");}
    finally{setBusy(false);}
  }
  return <article className="callout" aria-label="Run approved NoiseLabz suite">
    <h4>Run the NoiseLabz suite</h4>
    <p>{plan?.scope ?? "Load the reviewed plan before running."}</p>
    {plan&&<><p className="scope-note">{plan.case_ids.join(" · ")} · Chromium · maximum {plan.timeout_seconds} seconds</p>
      <label style={{display:"flex",gap:10,alignItems:"flex-start",marginTop:16}}><input type="checkbox" checked={approved} disabled={busy||active(run)} onChange={e=>setApproved(e.target.checked)}/><span>I reviewed and approve these fixed public UI checks.</span></label></>}
    <div className="action-row"><Button disabled={!plan||!approved||busy||active(run)} onClick={start}>{busy?"Starting…":active(run)?"Run in progress":"Run approved suite"}</Button><Button variant="outline" disabled={busy||active(run)} onClick={()=>setReload(v=>v+1)}>Reload run plan</Button></div>
    {run&&<p role="status">Run status: <strong>{run.state.replaceAll("_"," ")}</strong>{run.finished_at?` · ${new Date(run.finished_at).toLocaleString()}`:""}</p>}
    {run?.note&&<p className="scope-note">{run.note}</p>}
    {error&&<p role="alert">{error}</p>}
    <p className="scope-note">This runs the hand-written suite, independently of scenario edits in Review. Local single-user runner; no AI calls.</p>
  </article>;
}
