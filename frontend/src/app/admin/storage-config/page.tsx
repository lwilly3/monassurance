"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import * as Toast from "@radix-ui/react-toast";
import type { components } from "@/lib/api.types";

type StorageConfigRead = components["schemas"]["StorageConfigRead"];
type StorageConfigUpdate = components["schemas"]["StorageConfigUpdate"];
type BackendKind = StorageConfigUpdate["backend"];

export default function StorageConfigPage() {
  const [backend, setBackend] = useState<BackendKind>("local");
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveJsonPath, setGdriveJsonPath] = useState("");
  const [showJsonPath, setShowJsonPath] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [validationErrors, setValidationErrors] = useState<{ folder?: string; json?: string }>({});
  const [toastOpen, setToastOpen] = useState(false);
  const [toast, setToast] = useState<{ title: string; description?: string; kind: "success" | "error" }>({ title: "", kind: "success" });

  // Chargement initial de la configuration existante
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/v1/admin/storage-config");
        if (!res.ok) throw new Error("Lecture de la configuration impossible");
  const data: StorageConfigRead = await res.json();
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
    setValidationErrors({});

    // Validation UI
    if (backend === "google_drive") {
      const vErr: { folder?: string; json?: string } = {};
      if (!gdriveFolderId.trim()) vErr.folder = "Dossier requis";
      if (!gdriveJsonPath.trim()) vErr.json = "Chemin JSON requis";
      if (Object.keys(vErr).length) {
        setValidationErrors(vErr);
        setLoading(false);
        return;
      }
    }
    try {
  const body: StorageConfigUpdate = {
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
  setToast({ title: "Configuration enregistrée", description: "Mise à jour réussie", kind: "success" });
  setToastOpen(true);
  setTimeout(() => setSuccess(false), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
  setToast({ title: "Erreur", description: err instanceof Error ? err.message : "Erreur inconnue", kind: "error" });
  setToastOpen(true);
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
          <div>
            <Input
              label="ID du dossier Google Drive"
              value={gdriveFolderId}
              onChange={e => { setGdriveFolderId(e.target.value); setSuccess(false); if (validationErrors.folder) setValidationErrors(v => ({ ...v, folder: undefined })); }}
              required
              disabled={loading}
              className="mb-1"
            />
            {validationErrors.folder && <p className="text-sm text-red-600 mb-2" role="alert">{validationErrors.folder}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Chemin du fichier Service Account JSON</label>
            <div className="flex gap-2 items-start mb-1">
              <input
                type={showJsonPath ? "text" : "password"}
                value={gdriveJsonPath}
                onChange={e => { setGdriveJsonPath(e.target.value); setSuccess(false); if (validationErrors.json) setValidationErrors(v => ({ ...v, json: undefined })); }}
                disabled={loading}
                className="flex-1 p-2 border rounded"
                required
              />
              <Button
                type="button"
                onClick={() => setShowJsonPath(s => !s)}
                disabled={loading}
                className="bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                {showJsonPath ? "Masquer" : "Voir"}
              </Button>
            </div>
            {validationErrors.json && <p className="text-sm text-red-600 mb-2" role="alert">{validationErrors.json}</p>}
          </div>
        </>
      )}

      <Button type="submit" disabled={loading || (backend === "google_drive" && (!gdriveFolderId.trim() || !gdriveJsonPath.trim()))}>
        {loading ? "Enregistrement..." : "Enregistrer"}
      </Button>

  {error && <div className="text-red-600" role="alert">Erreur : {error}</div>}
  {success && <div className="text-green-600" role="status">Configuration enregistrée !</div>}

      {loading && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50" aria-live="polite" aria-busy="true">
          <div className="bg-white px-6 py-4 rounded shadow flex items-center gap-3">
            <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            <span>Enregistrement…</span>
          </div>
        </div>
      )}

      <Toast.Root
        open={toastOpen}
        onOpenChange={setToastOpen}
        className={`relative rounded-md px-4 py-3 pr-10 shadow-lg text-sm font-medium ${toast.kind === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"}`}
      >
        <Toast.Title className="font-semibold text-base">{toast.title}</Toast.Title>
        {toast.description && <Toast.Description className="mt-1 opacity-90">{toast.description}</Toast.Description>}
        <Toast.Close className="absolute right-2 top-2 text-white/80 hover:text-white" aria-label="Fermer">×</Toast.Close>
      </Toast.Root>
    </form>
  );
}
