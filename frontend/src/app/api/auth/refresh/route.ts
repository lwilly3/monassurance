import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export async function POST() {
  const c = await cookies();
  const token = c.get('refresh_token')?.value;
  if (!token) return NextResponse.json({ detail: 'No refresh token' }, { status: 401 });
  const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: token }),
  });
  const data = await res.json();
  if (!res.ok) {
    return NextResponse.json(data, { status: res.status });
  }
  c.set('refresh_token', data.refresh_token, { httpOnly: true, sameSite: 'lax', path: '/', secure: false });
  return NextResponse.json({ access_token: data.access_token });
}
