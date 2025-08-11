"use client";

export function LogoutButton() {
  const onClick = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  };
  return (
    <button onClick={onClick} className="bg-black text-white rounded px-3 py-2">Logout</button>
  );
}
