import { afterEach, describe, expect, it, vi } from 'vitest';
import { request } from './client';

afterEach(() => { vi.unstubAllGlobals(); });
describe('safe API boundary', () => {
  it('does not parse an internal server error as JSON', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Internal Server Error', { status: 500 })));
    await expect(request('/api/kpi/week')).rejects.toThrow(/non-JSON response \(HTTP 500\)/);
  });
  it('propagates a sanitized JSON API error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Quota reached' }), { status: 502 })));
    await expect(request('/api/ai/verify')).rejects.toThrow(/Quota reached/);
  });
  it('uses same-origin request, and never appends credentials to URL', async () => {
    const spy = vi.fn().mockResolvedValue(new Response('{"ok":true}', { status: 200 }));
    vi.stubGlobal('fetch', spy);
    await request('/api/ai/verify', { method:'POST', headers:{'X-Gemini-API-Key':'TEST_KEY_NOT_REAL_0000000000'}, body:'{"model":"gemini-2.5-flash"}' });
    expect(spy.mock.calls[0][0]).toBe('/api/ai/verify');
    expect(spy.mock.calls[0][1].headers['X-Gemini-API-Key']).toBe('TEST_KEY_NOT_REAL_0000000000');
    expect(spy.mock.calls[0][1].cache).toBe('no-store');
  });
});
