"use client";
import {useEffect,useState} from "react";
import {z} from "zod";

export function GeneratedEvidence({runId}:{runId:string}){
 const [artifacts,setArtifacts]=useState<string[]>([]),[error,setError]=useState("");
 const base=`/qa-api/generated-runs/${runId}/evidence`;
 useEffect(()=>{let mounted=true;setArtifacts([]);setError("");
 fetch(base,{signal:AbortSignal.timeout(10000)}).then(async r=>{if(!r.ok)throw Error();return z.object({artifacts:z.array(z.enum(["screenshot","trace"]))}).parse(await r.json());}).then(body=>{if(mounted)setArtifacts(body.artifacts);}).catch(()=>{if(mounted)setError("Evidence could not be loaded. Reload the review to try again.");});
 return()=>{mounted=false;};},[base]);
 return <section aria-label="Generated run evidence"><h4>Generated run evidence</h4><p className="scope-note">Run {runId}. The screenshot shows the final browser state; assertions and the trace explain the test result.</p>
 {artifacts.includes("screenshot")&&<a href={`${base}/screenshot`} target="_blank" rel="noreferrer"><img src={`${base}/screenshot`} alt="Final browser state from this generated NoiseLabz test" style={{width:"100%",borderRadius:12}}/></a>}
 {artifacts.includes("trace")&&<p><a href={`${base}/trace`}>Download Playwright trace</a></p>}
 {!artifacts.length&&!error&&<p>No browser artifacts available for this run.</p>}
 {error&&<p role="alert">{error}</p>}</section>;
}
