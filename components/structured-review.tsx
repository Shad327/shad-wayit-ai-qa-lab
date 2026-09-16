"use client";
import {ReviewEvaluation} from "@/components/review-evaluation";
import {RunSuite} from "@/components/run-suite";
import {useEffect,useState} from "react";
import {z} from "zod";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import {Textarea} from "@/components/ui/textarea";
const draftSchema=z.object({scenarios:z.array(z.object({title:z.string(),preconditions:z.array(z.string()),steps:z.array(z.object({action:z.string(),expected_result:z.string()})),source_ids:z.array(z.string())})),questions:z.array(z.string())});
const responseSchema=z.object({review:z.object({revision:z.number(),approved:z.boolean(),evidence_stale:z.boolean(),mode:z.enum(["demo_data","model_generated"]),draft:draftSchema,evidence:z.array(z.object({id:z.string(),text:z.string(),start_line:z.number(),end_line:z.number()}))}).nullable()});
type Draft=z.infer<typeof draftSchema>;
type Review=z.infer<typeof responseSchema>["review"];
export function StructuredReview({identifier}:{identifier:string}){
 const [saved,setSaved]=useState<Review>(null),[draft,setDraft]=useState<Draft|null>(null),[busy,setBusy]=useState(true),[error,setError]=useState("");
 const [preview,setPreview]=useState<{code:string;limitations:string}|null>(null);
 const dirty=JSON.stringify(draft)!==JSON.stringify(saved?.draft??null);
 function apply(body:unknown){setPreview(null);const {review}=responseSchema.parse(body);setSaved(review);setDraft(review?.draft??null);}
 useEffect(()=>{const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),10000);setBusy(true);fetch(`/qa-api/structured-reviews/${identifier}`,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(apply).catch(()=>{if(!controller.signal.aborted)setError("Could not load structured review. Start Python and reload.");}).finally(()=>{clearTimeout(timer);setBusy(false);});return()=>{clearTimeout(timer);controller.abort();};},[identifier]);
 async function send(action:string){setBusy(true);setError("");try{
 const r=await fetch(`/qa-api/structured-reviews/${identifier}${action?`/${action}`:""}`,{method:action==="reload"?"GET":action?"POST":"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({revision:saved?.revision??0,...(!action?{draft}:{})}),signal:AbortSignal.timeout(10000)});
 if(!r.ok){const body=z.object({detail:z.string()}).safeParse(await r.json());throw Error(body.success?body.data.detail:"Check required fields and source references before saving.");}apply(await r.json());
 }catch(e){setError(e instanceof Error?e.message:"Request failed");}finally{setBusy(false);}}
 async function reload(){setBusy(true);setError("");try{const r=await fetch(`/qa-api/structured-reviews/${identifier}`,{signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error("Cannot reload review");apply(await r.json());}catch(e){setError(String(e));}finally{setBusy(false);}}
 async function download(){if(!saved)return;setBusy(true);setError("");try{
 const r=await fetch(`/qa-api/structured-reviews/${identifier}/export?revision=${saved.revision}`,{signal:AbortSignal.timeout(10000)});
 if(!r.ok)throw Error("Export blocked. Reload the review and approve its current version with up-to-date evidence.");
 const body=await r.json();const url=URL.createObjectURL(new Blob([JSON.stringify(body,null,2)],{type:"application/json"}));const link=document.createElement("a");link.href=url;link.download=`approved-${identifier}-v${saved.revision}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }catch(e){setError(e instanceof Error?e.message:"Download failed");}finally{setBusy(false);}}
 async function generate(){if(!saved)return;setBusy(true);setError("");setPreview(null);try{
 const r=await fetch(`/qa-api/structured-reviews/${identifier}/test-preview?revision=${saved.revision}`,{signal:AbortSignal.timeout(10000)});const body=await r.json();
 if(!r.ok){const failure=z.object({detail:z.string()}).safeParse(body);throw Error(failure.success?failure.data.detail:"Preview failed");}
 setPreview(z.object({code:z.string(),limitations:z.string()}).parse(body));
 }catch(e){setError(e instanceof Error?e.message:"Preview failed");}finally{setBusy(false);}}
 async function downloadTest(){if(!saved||!preview)return;setBusy(true);setError("");try{
 const r=await fetch(`/qa-api/structured-reviews/${identifier}/test-preview?revision=${saved.revision}`,{signal:AbortSignal.timeout(10000)});
 if(!r.ok)throw Error("Download blocked. Reload and approve the current review, then preview again.");
 const body=z.object({code:z.string()}).parse(await r.json());
 if(body.code!==preview.code)throw Error("Generated code changed. Preview again before downloading.");
 const url=URL.createObjectURL(new Blob([body.code],{type:"text/x-python"}));const link=document.createElement("a");link.href=url;link.download="test_approved_guest_features.py";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }catch(e){setPreview(null);setError(e instanceof Error?e.message:"Download failed");}finally{setBusy(false);}}
 function change(edit:(d:Draft)=>void){if(!draft)return;setPreview(null);const copy=structuredClone(draft);edit(copy);setDraft(copy);}
 return <section aria-label="Structured scenario review"><p className="panel-description">{saved?.mode==="model_generated"?"Model-origin draft with possible human edits. Review every assertion against the evidence.":"Sample data · hand-written, not AI-generated. Review test steps, expected results, and source references in the format the model will use."}</p>
 {!saved&&<Button disabled={busy} onClick={()=>send("sample")}>Create structured sample</Button>}
 {draft&&<><fieldset disabled={busy} style={{border:0,padding:0}}>{draft.scenarios.map((scenario,i)=><article key={i} className="callout">
 <label>Test title<Input value={scenario.title} maxLength={2000} onChange={e=>change(d=>{d.scenarios[i].title=e.target.value;})}/></label>
 <label>Preconditions (one per line)<Textarea aria-label="Preconditions (one per line)" value={scenario.preconditions.join("\n")} onChange={e=>change(d=>{d.scenarios[i].preconditions=e.target.value?e.target.value.split("\n"):[];})}/></label>
 {scenario.steps.map((step,j)=><div key={j} style={{borderTop:"1px solid #34404d",paddingTop:16,marginTop:16}}><strong>Step {j+1}</strong>
 <label>Action {j+1}<Textarea aria-label={`Action ${j+1}`} value={step.action} maxLength={2000} onChange={e=>change(d=>{d.scenarios[i].steps[j].action=e.target.value;})}/></label>
 <label>Expected result {j+1}<Textarea aria-label={`Expected result ${j+1}`} value={step.expected_result} maxLength={2000} onChange={e=>change(d=>{d.scenarios[i].steps[j].expected_result=e.target.value;})}/></label>
 <Button variant="ghost" disabled={scenario.steps.length<=1} onClick={()=>change(d=>{d.scenarios[i].steps.splice(j,1);})}>Remove step {j+1}</Button></div>)}
 {identifier==="AUTH-04"&&<label>Add supported navigation<select aria-label="Add supported navigation" value="" onChange={e=>{const label=e.target.value;if(label)change(d=>{d.scenarios[i].steps.push({action:`Select ${label}`,expected_result:`${label} section is visible`});});}}><option value="">Choose a section</option>{["About Us","How It Works","Roadmap"].filter(label=>!scenario.steps.some(s=>s.action===`Select ${label}`)).map(label=><option key={label}>{label}</option>)}</select></label>}
 <Button variant="outline" disabled={scenario.steps.length>=15} onClick={()=>change(d=>{d.scenarios[i].steps.push({action:"",expected_result:""});})}>Add step</Button>
 <label style={{marginTop:16}}>Source IDs (comma separated)<Input value={scenario.source_ids.join(",")} onChange={e=>change(d=>{d.scenarios[i].source_ids=e.target.value.split(",").map(x=>x.trim());})}/></label>
 </article>)}<label>Open questions (one per line)<Textarea aria-label="Open questions (one per line)" value={draft.questions.join("\n")} onChange={e=>change(d=>{d.questions=e.target.value?e.target.value.split("\n"):[];})}/></label></fieldset>
 <p role="status">{dirty?"Unsaved changes · approval does not cover these edits":saved?.evidence_stale?"Source changed · refresh evidence and review again":saved?.approved?`Structured version ${saved.revision} approved`:`Structured version ${saved?.revision} awaiting approval`}</p>
 <div className="action-row"><Button disabled={busy||!dirty} onClick={()=>send("")}>Save structured changes</Button><Button disabled={busy||dirty||saved?.approved||saved?.evidence_stale} onClick={()=>send("approve")}>Approve structured version</Button><Button variant="outline" disabled={busy||dirty} onClick={()=>send("refresh-evidence")}>Refresh structured evidence</Button><Button disabled={busy||dirty||!saved?.approved||saved?.evidence_stale} onClick={download}>Download approved package</Button><Button disabled={busy||dirty||!saved?.approved||saved?.evidence_stale} onClick={generate}>Preview Python test</Button></div>
 {preview&&<section aria-label="Generated test preview"><h3>Template-generated Python · not executed</h3><p>{preview.limitations}</p><Button disabled={busy||dirty||!saved?.approved||saved?.evidence_stale} onClick={downloadTest}>Download Python test</Button><p>Save the file in browser_tests, then run from the project folder:</p><pre>.venv/bin/python -m pytest browser_tests/test_approved_guest_features.py --browser chromium -v</pre><pre style={{overflowX:"auto"}}><code>{preview.code}</code></pre>{identifier==="AUTH-04"&&saved&&<RunSuite generated={{code:preview.code,revision:saved.revision}} onComplete={()=>{}}/>}</section>}
 {saved&&!dirty&&<ReviewEvaluation identifier={identifier} revision={saved.revision}/>}
 {saved?.evidence.map(p=><details key={p.id} className="scope-note"><summary>Source {p.id} · lines {p.start_line}–{p.end_line}</summary><blockquote>{p.text}</blockquote></details>)}
 <p className="scope-note">Approval applies to this saved version and source snapshot. It does not generate code or approve the separate fixed NoiseLabz suite. Open questions remain visible for human review.</p></>}
 {error&&<p role="alert" className="callout">{error}</p>}
 <Button variant="ghost" disabled={busy} onClick={reload}>Reload structured review (replaces unsaved edits)</Button>
 </section>;
}
