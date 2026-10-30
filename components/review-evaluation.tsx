"use client";
import {useEffect,useState} from "react";
import {z} from "zod";
const schema=z.object({revision:z.number(),status:z.string(),checks:z.array(z.object({name:z.string(),status:z.enum(["passed","failed","review"]),detail:z.string()}))});
export function ReviewEvaluation({identifier,revision}:{identifier:string;revision:number}){
 const [result,setResult]=useState<z.infer<typeof schema>|null>(null),[error,setError]=useState("");
 useEffect(()=>{let active=true;setResult(null);setError("");fetch(`/qa-api/structured-reviews/${identifier}/evaluation`,{signal:AbortSignal.timeout(10000)}).then(async r=>{if(!r.ok)throw Error();return schema.parse(await r.json());}).then(r=>{if(active){if(r.revision!==revision)throw Error();setResult(r);}}).catch(()=>{if(active)setError('Evaluation unavailable or review changed. Reload the saved review.');});return()=>{active=false;};},[identifier,revision]);
 return <section className="callout" aria-label="Scenario evaluation"><h4>Saved scenario evaluation</h4><p>Deterministic checks · no LLM judge. Results apply to saved version {revision}.</p>{result?.checks.map(c=><p key={c.name}><strong>{c.name}: {c.status}</strong><br/>{c.detail}</p>)}{error&&<p role="alert">{error}</p>}</section>;
}
