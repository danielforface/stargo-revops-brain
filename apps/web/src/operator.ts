/** Pure operator view and inbound timestamp helpers, testable without the browser. */
export type InboundForm = {from_name:string;from_email:string;linkedin_url:string;channel:string;source:string;received_at:string;body:string};
export function inboundPayload(form: InboundForm) {
  const receivedAt = form.received_at.trim();
  if (receivedAt && Number.isNaN(new Date(receivedAt).getTime())) throw new Error('Invalid received time.');
  return {
    from_name:form.from_name.trim(), from_email:form.from_email.trim() || null,
    linkedin_url:form.linkedin_url.trim() || null, channel:form.channel,
    source:form.source.trim() || null, body:form.body,
    ...(receivedAt ? {received_at: new Date(receivedAt).toISOString()} : {}),
  };
}
export function leadSummary(leads: any[]) {
  return { identities: leads.length,
    touches:leads.reduce((n,lead)=>n+(Number(lead.touch_count)||1),0),
    currentQualified:leads.filter(lead=>lead.analysis?.qualification?.status==='QL').length };
}
