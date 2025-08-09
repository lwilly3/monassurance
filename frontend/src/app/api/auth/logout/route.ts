import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export async function POST() {
  const c = await cookies();
  const token = c.get('refresh_token')?.value;
  if (token) {
    await fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: token }),
    }).catch(() => {});
    c.delete('refresh_token');
  }
  return NextResponse.json({ ok: true });
}
