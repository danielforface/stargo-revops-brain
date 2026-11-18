import {describe, it, expect} from 'vitest';
import {inboundPayload, leadSummary} from './operator';
const form = {from_name:' Buyer ', from_email:' buyer@example.com ', linkedin_url:'', channel:'email_reply',source:'',received_at:'',body:'Can we see a demo?'};
describe('operator inputs',()=>{
  it('omits received time and source when empty',()=>{
    const payload = inboundPayload(form);
    expect(payload).not.toHaveProperty('received_at');
    expect(payload.from_name).toBe('Buyer');
    expect(payload.source).toBeNull();
  });
  it('converts explicit local time into a UTC timestamp',()=>{
    const payload = inboundPayload({...form,received_at:'2026-10-07T12:00'});
    expect(new Date(payload.received_at!).getTime()).toBe(new Date('2026-10-07T12:00').getTime());
  });
  it('rejects invalid times before any request',()=>{
    expect(()=>inboundPayload({...form,received_at:'not-a-date'})).toThrow('Invalid received time');
  });
  it('distinguishes people from inbound events and current status',()=>{
    const leads=[{touch_count:2,analysis:{qualification:{status:'QL'}}},{touch_count:1,analysis:{qualification:{status:'QL candidate'}}}];
    expect(leadSummary(leads)).toEqual({identities:2,touches:3,currentQualified:1});
  });
});
