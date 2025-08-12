"use client";
import { useState, useEffect, useCallback } from "react";
import type { components } from "@/lib/api.types";

type StorageConfigRead = components["schemas"]["StorageConfigRead"];
type StorageConfigUpdate = components["schemas"]["StorageConfigUpdate"];
export type BackendKind = StorageConfigUpdate["backend"];

interface UseStorageConfigResult {
  backend: BackendKind;
  gdriveFolderId: string;
  gdriveJsonPath: string;
  setBackend: (b: BackendKind) => void;
  setGdriveFolderId: (v: string) => void;
  setGdriveJsonPath: (v: string) => void;
  loading: boolean;
  saving: boolean;
  error: string | null;
  success: boolean;
  resetSuccess: () => void;
  save: () => Promise<void>;
  validate: () => boolean;
}

export function useStorageConfig(): UseStorageConfigResult {
  const [backend, setBackend] = useState<BackendKind>("local");
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveJsonPath, setGdriveJsonPath] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/v1/admin/storage-config");
        if (!res.ok) throw new Error("Fetch config failed");
        const data: StorageConfigRead = await res.json();
        if (cancelled) return;
        setBackend(data.backend);
        setGdriveFolderId(data.gdrive_folder_id || "");
        setGdriveJsonPath(data.gdrive_service_account_json_path || "");
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erreur");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const validate = useCallback(() => {
    if (backend === "google_drive") {
      return !!gdriveFolderId.trim() && !!gdriveJsonPath.trim();
    }
    return true;
  }, [backend, gdriveFolderId, gdriveJsonPath]);

  const save = useCallback(async () => {
    setSaving(true);
    setError(null);
    // Optimistic update: on marque le succès immédiatement; rollback si erreur
    setSuccess(true);
    const prev = { backend, gdriveFolderId, gdriveJsonPath };
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
      // Confirmation finale: on laisse le succès et timer reset
      setTimeout(() => setSuccess(false), 4000);
    } catch (e) {
      // Rollback visuel: on rétablit les valeurs précédentes
      setBackend(prev.backend);
      setGdriveFolderId(prev.gdriveFolderId);
      setGdriveJsonPath(prev.gdriveJsonPath);
      setSuccess(false);
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    } finally {
      setSaving(false);
    }
  }, [backend, gdriveFolderId, gdriveJsonPath]);

  return {
    backend,
    gdriveFolderId,
    gdriveJsonPath,
    setBackend,
    setGdriveFolderId,
    setGdriveJsonPath,
    loading,
    saving,
    error,
    success,
    resetSuccess: () => setSuccess(false),
    save,
    validate,
  };
}
