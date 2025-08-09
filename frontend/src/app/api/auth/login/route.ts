import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    return NextResponse.json(data, { status: res.status });
  }
  const c = await cookies();
  // Stocker refresh_token en httpOnly; access_token côté mémoire (renvoyé au client)
  c.set('refresh_token', data.refresh_token, { httpOnly: true, sameSite: 'lax', path: '/', secure: false });
  return NextResponse.json({ access_token: data.access_token });
}
