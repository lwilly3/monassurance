export class AuthClient {
  private accessToken: string | null = null;

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  async fetch<T>(input: RequestInfo, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    if (this.accessToken) {
      headers.set('Authorization', `Bearer ${this.accessToken}`);
    }
    let res = await fetch(input, { ...init, headers, credentials: 'include' });
    if (res.status === 401) {
      // tenter un refresh
      const r = await fetch('/api/auth/refresh', { method: 'POST' });
      if (r.ok) {
        const data = (await r.json()) as { access_token: string };
        this.accessToken = data.access_token;
        headers.set('Authorization', `Bearer ${this.accessToken}`);
        res = await fetch(input, { ...init, headers, credentials: 'include' });
      }
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `HTTP ${res.status}`);
    }
    return res.json() as Promise<T>;
  }
}

export const authClient = new AuthClient();
