/** Single API boundary: report HTTP failures without assuming they are JSON. */
export async function request(url: string, options?: RequestInit): Promise<any> {
  const response = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options?.headers as Record<string, string> | undefined) },
    cache: 'no-store',
  });
  const raw = await response.text();
  let result: any;
  try {
    result = raw ? JSON.parse(raw) : null;
  } catch {
    throw new Error(`Server returned a non-JSON response (HTTP ${response.status}) for ${url}. Review the Backend terminal.`);
  }
  if (!response.ok) {
    const detail = typeof result?.detail === 'string' ? result.detail : `Server request failed (HTTP ${response.status})`;
    throw new Error(`${detail} · ${url}`);
  }
  return result;
}
