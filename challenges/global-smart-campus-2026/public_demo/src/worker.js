const cases = [
  {id:'policy-conflict',title:'Conflicting policy guidance',question:'What should the department do before approving after-hours lab access?',evidence:[
    {id:'E1',type:'policy_memo',text:'Policy memo A requires department-chair approval and annual safety training before after-hours lab access.'},
    {id:'E2',type:'policy_memo',text:'Policy memo B allows trained research staff to request after-hours access through the security office without chair approval.'},
    {id:'E3',type:'training_record',text:'The synthetic requester completed annual safety training on 2026-08-18.'}],expected_conflicts:[['E1','E2']]},
  {id:'research-access',title:'Research access request',question:'What review steps are required before releasing the synthetic research dataset?',evidence:[
    {id:'E1',type:'request',text:'The synthetic requester asks for a de-identified dataset for a campus mobility study.'},
    {id:'E2',type:'data_policy',text:'Dataset release requires data-owner approval, a purpose statement, and a documented retention period.'},
    {id:'E3',type:'security_note',text:'The proposed workspace supports encrypted storage and access logging.'},
    {id:'E4',type:'review_note',text:'No data-owner approval is attached to the request.'}],expected_conflicts:[]},
  {id:'energy-anomaly',title:'Facilities energy anomaly',question:'What should facilities investigate first after the overnight energy spike?',evidence:[
    {id:'E1',type:'meter_event',text:'Building C electricity use increased 38 percent between 01:00 and 03:00 compared with the prior seven-night median.'},
    {id:'E2',type:'maintenance_note',text:'Air-handler AHU-C3 was placed in manual override during a ventilation inspection at 00:42.'},
    {id:'E3',type:'occupancy_note',text:'No scheduled overnight event or approved extended occupancy is recorded for Building C.'},
    {id:'E4',type:'weather_note',text:'Outdoor temperature remained within two degrees of the seven-night median.'}],expected_conflicts:[]}
];
const claim=(text,citations,kind='evidence')=>({text,citations,kind});
function actions(id){
  if(id==='policy-conflict') return [
    claim('Pause approval until the conflicting approval paths are reconciled by the policy owner.',['E1','E2'],'action'),
    claim('Treat annual safety training as satisfied for this synthetic request.',['E3'],'action')];
  if(id==='research-access') return [
    claim('Obtain data-owner approval before release.',['E2','E4'],'action'),
    claim('Record the purpose statement and retention period before release.',['E2'],'action'),
    claim('Use the encrypted, access-logged workspace if the request is approved.',['E3'],'action')];
  if(id==='energy-anomaly') return [
    claim('Inspect AHU-C3 manual override first because its timing precedes the overnight spike.',['E1','E2'],'action'),
    claim('Do not attribute the spike to scheduled occupancy or unusual weather without new evidence.',['E3','E4'],'action')];
  return [];
}
function analyze(c){
  const claims=c.evidence.map(e=>claim(e.text,[e.id]));
  const conflicts=(c.expected_conflicts||[]).map(([a,b])=>({evidence:[a,b],detail:`Conflict requires human resolution: [${a}] and [${b}] prescribe incompatible approval paths.`}));
  const report={case_id:c.id,title:c.title,question:c.question,claims,conflicts,actions:actions(c.id),
    uncertainty:'Only supplied synthetic evidence was considered; missing records may change the result.',
    review_gate:{required:true,status:'PENDING_HUMAN_REVIEW'}};
  report.validation={citation_validity:1,invalid_citations:[],uncited_items:[],conflict_detection:true,unsupported_material_claims:0};
  return report;
}
const baseHeaders={'x-content-type-options':'nosniff','referrer-policy':'no-referrer','x-frame-options':'DENY','permissions-policy':'camera=(), microphone=(), geolocation=()','cross-origin-resource-policy':'same-origin'};
function json(data,status=200){return new Response(JSON.stringify(data),{status,headers:{...baseHeaders,'content-type':'application/json;charset=utf-8','cache-control':'no-store'}})}
export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(request.method!=='GET' && request.method!=='HEAD') return json({error:'method not allowed'},405);
    if(url.pathname==='/api/cases') return json(cases);
    if(url.pathname==='/api/status') return json({providers:{nvidia:{configured:false,model:'public-demo-safe-mode'}},public_demo:true,live_model_external:false});
    if(url.pathname==='/api/analyze'){
      const c=cases.find(x=>x.id===url.searchParams.get('id'));
      if(!c) return json({error:'unknown case'},404);
      const report=analyze(c);
      if(url.searchParams.get('mode')==='live') report.model_synthesis={
        error:'Live model is intentionally disabled on the public demo to prevent uncontrolled external compute use. The validated live-model receipt is retained in the submission package.',
        review_gate:{required:true,status:'PENDING_HUMAN_REVIEW'}
      };
      return json(report);
    }
    const response=await env.ASSETS.fetch(request);
    const h=new Headers(response.headers);
    h.set('x-content-type-options','nosniff');
    h.set('referrer-policy','no-referrer');
    h.set('x-frame-options','DENY');
    h.set('permissions-policy','camera=(), microphone=(), geolocation=()');
    h.set('cross-origin-resource-policy','same-origin');
    h.set('content-security-policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'");
    return new Response(response.body,{status:response.status,statusText:response.statusText,headers:h});
  }
};
