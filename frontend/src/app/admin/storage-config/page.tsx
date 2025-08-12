"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

type BackendKind = "local" | "google_drive";

interface StorageConfig {
  backend: BackendKind;
  gdrive_folder_id?: string | null;
  gdrive_service_account_json_path?: string | null;
}

export default function StorageConfigPage() {
  const [backend, setBackend] = useState<BackendKind>("local");
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveJsonPath, setGdriveJsonPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Chargement initial de la configuration existante
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/v1/admin/storage-config");
        if (!res.ok) throw new Error("Lecture de la configuration impossible");
        const data: StorageConfig = await res.json();
        if (cancelled) return;
        setBackend(data.backend);
        setGdriveFolderId(data.gdrive_folder_id || "");
        setGdriveJsonPath(data.gdrive_service_account_json_path || "");
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erreur de chargement");
      } finally {
        if (!cancelled) setFetching(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const body: StorageConfig = {
        backend,
        gdrive_folder_id: backend === "google_drive" ? gdriveFolderId : null,
        gdrive_service_account_json_path: backend === "google_drive" ? gdriveJsonPath : null,
      };
      const res = await fetch("/api/v1/admin/storage-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return <div className="max-w-lg mx-auto mt-8 p-6">Chargement…</div>;
  }

  return (
    <form
      className="max-w-lg mx-auto mt-8 p-6 bg-white rounded shadow space-y-4"
      onSubmit={handleSubmit}
      aria-labelledby="storage-config-title"
    >
      <h2 id="storage-config-title" className="text-xl font-bold">Configuration du stockage</h2>

      <div>
        <label className="block mb-2 font-medium" htmlFor="backend">Backend</label>
        <select
          id="backend"
          value={backend}
          onChange={e => { setBackend(e.target.value as BackendKind); setSuccess(false); }}
          className="p-2 border rounded w-full"
          disabled={loading}
        >
          <option value="local">Local</option>
          <option value="google_drive">Google Drive</option>
        </select>
      </div>

      {backend === "google_drive" && (
        <>
          <Input
            label="ID du dossier Google Drive"
            value={gdriveFolderId}
            onChange={e => { setGdriveFolderId(e.target.value); setSuccess(false); }}
            required
            disabled={loading}
            className="mb-2"
          />
          <Input
            label="Chemin du fichier Service Account JSON"
            value={gdriveJsonPath}
            onChange={e => { setGdriveJsonPath(e.target.value); setSuccess(false); }}
            required
            disabled={loading}
            className="mb-2"
          />
        </>
      )}

      <Button type="submit" disabled={loading}>
        {loading ? "Enregistrement..." : "Enregistrer"}
      </Button>

      {error && <div className="text-red-600" role="alert">Erreur : {error}</div>}
      {success && <div className="text-green-600" role="status">Configuration enregistrée !</div>}
    </form>
  );
}
