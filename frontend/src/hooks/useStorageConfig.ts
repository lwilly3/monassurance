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
  s3Bucket: string;
  s3Region: string;
  s3EndpointUrl: string;
  setBackend: (b: BackendKind) => void;
  setGdriveFolderId: (v: string) => void;
  setGdriveJsonPath: (v: string) => void;
  setS3Bucket: (v: string) => void;
  setS3Region: (v: string) => void;
  setS3EndpointUrl: (v: string) => void;
  loading: boolean;
  saving: boolean;
  error: string | null;
  success: boolean;
  resetSuccess: () => void;
  save: () => Promise<{ ok: boolean; error?: string }>;
  validate: () => boolean;
}

export function useStorageConfig(): UseStorageConfigResult {
  const [backend, setBackend] = useState<BackendKind>("local");
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveJsonPath, setGdriveJsonPath] = useState("");
  const [s3Bucket, setS3Bucket] = useState("");
  const [s3Region, setS3Region] = useState("");
  const [s3EndpointUrl, setS3EndpointUrl] = useState("");
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
  setS3Bucket(data.s3_bucket || "");
  setS3Region(data.s3_region || "");
  setS3EndpointUrl(data.s3_endpoint_url || "");
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
    if (backend === "s3") {
      return !!s3Bucket.trim();
    }
    return true;
  }, [backend, gdriveFolderId, gdriveJsonPath, s3Bucket]);

  const save = useCallback(async (): Promise<{ ok: boolean; error?: string }> => {
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
        s3_bucket: backend === "s3" ? s3Bucket : null,
        s3_region: backend === "s3" ? (s3Region || null) : null,
        s3_endpoint_url: backend === "s3" ? (s3EndpointUrl || null) : null,
      };
      const res = await fetch("/api/v1/admin/storage-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      // Confirmation finale: on laisse le succès et timer reset
      setTimeout(() => setSuccess(false), 4000);
      return { ok: true };
    } catch (e) {
      // Rollback visuel: on rétablit les valeurs précédentes
      setBackend(prev.backend);
      setGdriveFolderId(prev.gdriveFolderId);
      setGdriveJsonPath(prev.gdriveJsonPath);
      setSuccess(false);
      setError(e instanceof Error ? e.message : "Erreur inconnue");
      return { ok: false, error: e instanceof Error ? e.message : "Erreur inconnue" };
    } finally {
      setSaving(false);
    }
  }, [backend, gdriveFolderId, gdriveJsonPath, s3Bucket, s3Region, s3EndpointUrl]);

  return {
    backend,
    gdriveFolderId,
    gdriveJsonPath,
    setBackend,
    setGdriveFolderId,
  setGdriveJsonPath,
  s3Bucket,
  s3Region,
  s3EndpointUrl,
  setS3Bucket,
  setS3Region,
  setS3EndpointUrl,
    loading,
    saving,
    error,
    success,
    resetSuccess: () => setSuccess(false),
    save,
    validate,
  };
}
