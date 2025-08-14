"use client";
import { useState } from "react";

export default function AdminTestPage() {
  const [loginResult, setLoginResult] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const testAdminLogin = async () => {
    setLoading(true);
    setLoginResult("");
    
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          email: "admin@monassurance.com", 
          password: "D3faultpass" 
        }),
      });
      
      if (res.ok) {
        const data = await res.json();
        setLoginResult(`✅ Connexion admin réussie ! Token: ${data.access_token.substring(0, 50)}...`);
      } else {
        const error = await res.json();
        setLoginResult(`❌ Erreur: ${error.detail || "Connexion échouée"}`);
      }
    } catch (err) {
      setLoginResult(`❌ Erreur réseau: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  const testHealthEndpoint = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setLoginResult(`✅ Backend accessible ! Status: ${data.status}`);
      } else {
        setLoginResult(`❌ Backend non accessible: ${res.status}`);
      }
    } catch (err) {
      setLoginResult(`❌ Erreur connexion backend: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">🧪 Test Administrateur MonAssurance</h1>
        
        <div className="bg-gray-100 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Informations Admin Par Défaut</h2>
          <div className="space-y-2 font-mono text-sm">
            <div><strong>Email:</strong> admin@monassurance.com</div>
            <div><strong>Mot de passe:</strong> D3faultpass</div>
            <div><strong>Rôle:</strong> ADMIN</div>
          </div>
          <div className="mt-4 p-3 bg-yellow-100 rounded text-sm">
            ⚠️ <strong>Important:</strong> Changez ce mot de passe après la première connexion !
          </div>
        </div>

        <div className="space-y-4">
          <button
            onClick={testHealthEndpoint}
            disabled={loading}
            className="w-full p-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Test en cours..." : "🔗 Tester Connexion Backend"}
          </button>
          
          <button
            onClick={testAdminLogin}
            disabled={loading}
            className="w-full p-3 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? "Test en cours..." : "🔐 Tester Connexion Admin"}
          </button>
          
          <a
            href="/login"
            className="block w-full p-3 bg-purple-600 text-white rounded text-center hover:bg-purple-700"
          >
            📋 Aller à la page de Login
          </a>
        </div>

        {loginResult && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-semibold mb-2">Résultat du Test:</h3>
            <pre className="text-sm whitespace-pre-wrap">{loginResult}</pre>
          </div>
        )}

        <div className="mt-8 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold mb-2">🚀 Instructions d'utilisation:</h3>
          <ol className="list-decimal list-inside space-y-1 text-sm">
            <li>Testez d'abord la connexion backend</li>
            <li>Testez ensuite la connexion admin avec les identifiants par défaut</li>
            <li>Utilisez la page de login pour vous connecter manuellement</li>
            <li>Changez le mot de passe après la première connexion</li>
          </ol>
        </div>

        <div className="mt-6 p-4 bg-green-50 rounded-lg">
          <h3 className="font-semibold mb-2">🔧 Commandes utiles:</h3>
          <div className="space-y-1 text-sm font-mono">
            <div>python change_admin_password.py</div>
            <div>python test_admin_auth.py</div>
          </div>
        </div>
      </div>
    </div>
  );
}
