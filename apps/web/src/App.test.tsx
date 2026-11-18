// @vitest-environment jsdom
import React from 'react';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {render, screen, waitFor, fireEvent, cleanup} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {App} from './App';

const leads = [
  {inbound:{id:'I-1',from_name:'Test Buyer',from_email:'buyer@example.com',channel:'email_reply',received_at:'2026-10-06T09:00:00+03:00',body:'We need invoice reconciliation, please show a demo.',source:'event-email'},
   contact_id:'C-1',contact:{company_name:'Example Freight'},touch_count:2,
   analysis:{mode:'rules-only',extraction:null,qualification:{status:'QL',score:100,owner:'Leo',conditions:{},factors:{},rationale:'test'}}},
  {inbound:{id:'I-2',from_name:'Review Lead',from_email:'lead@example.com',channel:'form_fill',received_at:'2026-10-06T09:00:00+03:00',body:'Hello',source:null},
   contact_id:'C-2',contact:{company_name:'Unknown'},touch_count:1,
   analysis:{mode:'failed',extraction:null,qualification:{status:'needs review',score:0,owner:'Triage',conditions:{},factors:{},rationale:'test'}}},
];
const kpi = { metrics:{qualified_leads:{actual:1,target:25,variance:-24,records:[{id:'D-1',contact_id:'C-1',decided_at:'2026-10-07T10:00:00+03:00',rule:'frozen'}]},meetings_booked:{actual:0,target:15,variance:-15,records:[]},meetings_held:{actual:0,target:12,variance:-12,records:[]},opportunities_created:{actual:0,target:5,variance:-5,records:[]}}, by_source:{'event-email':{actual:1}},unknown_feeds:['historical-reactivation'],expansion:{qualified_leads:{actual:0},meetings_booked:{actual:0},meetings_held:{actual:0},opportunities_created:{actual:0}}};
const visibility = {formula:'Synthetic benchmark',answers:[],gaps:[{prompt_id:'P1',prompt:'freight AI visibility',priority:1,engines:[],score:70}]};
let captured:any[]=[];
const response=(value:any,status=200)=>new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});
beforeEach(()=>{
  captured=[];
  vi.stubGlobal('fetch',vi.fn().mockImplementation(async (url:string,options?:RequestInit)=>{
    captured.push({url,options});
    if(url==='/api/leads') return response(leads);
    if(url==='/api/kpi/week') return response(kpi);
    if(url==='/api/visibility') return response(visibility);
    if(url==='/api/ai/verify') return response({connected:true,provider:'gemini',mode:'live'});
    if(url.startsWith('/api/inbound')) return response({...leads[0],inbound:{...leads[0].inbound,id:'I-3',from_name:'New Buyer'}},201);
    if(url==='/api/kpi/pack') return response({markdown:'# Reporting pack\n\n1 QL'});
    if(url.startsWith('/api/leads/I-')) return response(leads[0]);
    return response({detail:'Unknown mock endpoint'},404);
  }));
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

describe('reviewer journeys',()=>{
  it('shows unique people separate from inbound events and current statuses',async()=>{
    render(<App/>);
    expect(await screen.findByText('UNIQUE LEADS')).toBeTruthy();
    expect(screen.getByText('INBOUND EVENTS')).toBeTruthy();
    const strip=document.querySelector('.metric-strip')!;
    expect(strip.textContent).toContain('UNIQUE LEADS2');
    expect(strip.textContent).toContain('INBOUND EVENTS3');
    expect(strip.textContent).toContain('CURRENT QL1');
    expect(screen.getByText(/Historical QLs are counted/i)).toBeTruthy();
  });
  it('submits a historical inbound from UI with an explicit timezone and no key',async()=>{
    const user=userEvent.setup();
    render(<App/>);
    await user.click(await screen.findByRole('button',{name:/New inbound/i}));
    fireEvent.change(screen.getByLabelText('Sender name'),{target:{value:'New Buyer'}});
    fireEvent.change(screen.getByLabelText('Email address (optional)'),{target:{value:'new@example.com'}});
    fireEvent.change(screen.getByLabelText(/Received at \(optional\)/i),{target:{value:'2026-10-06T09:00'}});
    fireEvent.change(screen.getByLabelText('Message text'),{target:{value:'We need an invoice demo.'}});
    await user.click(screen.getByRole('button',{name:/Save & analyze/i}));
    await waitFor(()=>expect(captured.some(x=>x.url.startsWith('/api/inbound'))).toBe(true));
    const event=captured.find(x=>x.url.startsWith('/api/inbound'));
    const payload=JSON.parse(event.options.body);
    expect(payload.received_at).toBe(new Date('2026-10-06T09:00').toISOString());
    expect(payload.from_email).toBe('new@example.com');
    expect(event.options.headers['X-Gemini-API-Key']).toBeUndefined();
  });
  it('connects Google in memory through local proxy only',async()=>{
    const user=userEvent.setup();
    render(<App/>);
    await user.click(await screen.findByRole('button',{name:/Configure Gemini AI/i}));
    const key='AQ.'+'A'.repeat(40);
    await user.type(screen.getByPlaceholderText(/Paste your Gemini API key/i),key);
    await user.click(screen.getByRole('button',{name:/Test connection & activate/i}));
    await waitFor(()=>expect(captured.some(x=>x.url==='/api/ai/verify')).toBe(true));
    const verify=captured.find(x=>x.url==='/api/ai/verify');
    expect(verify.options.headers['X-Gemini-API-Key']).toBe(key);
    expect(verify.url).not.toContain(key);
    expect(localStorage.length).toBe(0);
  });
});
