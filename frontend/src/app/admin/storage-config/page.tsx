"use client";

import { useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import * as Toast from "@radix-ui/react-toast";
import { useStorageConfig, BackendKind } from "@/hooks/useStorageConfig";

export default function StorageConfigPage() {
  const { backend, gdriveFolderId, gdriveJsonPath, setBackend, setGdriveFolderId, setGdriveJsonPath, loading: fetching, saving: loading, error, success, save, validate, resetSuccess } = useStorageConfig();
  const [showJsonPath, setShowJsonPath] = useState(false);
  const [toastOpen, setToastOpen] = useState(false);
  const [toast, setToast] = useState<{ title: string; description?: string; kind: "success" | "error" }>({ title: "", kind: "success" });
  const [validationErrors, setValidationErrors] = useState<{ folder?: string; json?: string }>({});
  const [lang] = useState<'fr' | 'en'>('fr');

  const t = (key: string): string => {
    const dict: Record<string, { fr: string; en: string }> = {
      title: { fr: 'Configuration du stockage', en: 'Storage configuration' },
      backend: { fr: 'Backend', en: 'Backend' },
      local: { fr: 'Local', en: 'Local' },
      gdrive: { fr: 'Google Drive', en: 'Google Drive' },
      folderId: { fr: 'ID du dossier Google Drive', en: 'Google Drive folder ID' },
      jsonPath: { fr: 'Chemin du fichier Service Account JSON', en: 'Service Account JSON file path' },
      save: { fr: 'Enregistrer', en: 'Save' },
      saving: { fr: 'Enregistrement...', en: 'Saving...' },
      saved: { fr: 'Configuration enregistrée !', en: 'Configuration saved!' },
      requiredFolder: { fr: 'Dossier requis', en: 'Folder required' },
      requiredJson: { fr: 'Chemin JSON requis', en: 'JSON path required' },
      show: { fr: 'Voir', en: 'Show' },
      hide: { fr: 'Masquer', en: 'Hide' },
      loading: { fr: 'Chargement…', en: 'Loading…' },
      updatedToast: { fr: 'Configuration enregistrée', en: 'Configuration saved' },
      updatedDesc: { fr: 'Mise à jour réussie', en: 'Update succeeded' },
      error: { fr: 'Erreur', en: 'Error' },
    };
    return dict[key]?.[lang] || key;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationErrors({});
    if (backend === 'google_drive') {
      const vErr: { folder?: string; json?: string } = {};
      if (!gdriveFolderId.trim()) vErr.folder = t('requiredFolder');
      if (!gdriveJsonPath.trim()) vErr.json = t('requiredJson');
      if (Object.keys(vErr).length) {
        setValidationErrors(vErr);
        return;
      }
    }
    const result = await save();
    if (result.ok) {
      setToast({ title: t('updatedToast'), description: t('updatedDesc'), kind: 'success' });
    } else {
      setToast({ title: t('error'), description: result.error, kind: 'error' });
    }
    setToastOpen(true);
  };

  if (fetching) {
    return <div data-testid="storage-config-loading" className="max-w-lg mx-auto mt-8 p-6">{t('loading')}</div>;
  }

  return (
    <form
      className="max-w-lg mx-auto mt-8 p-6 bg-white rounded shadow space-y-4"
      onSubmit={handleSubmit}
      aria-labelledby="storage-config-title"
    >
  <h2 id="storage-config-title" data-testid="storage-config-title" className="text-xl font-bold">{t('title')}</h2>

      <div>
  <label className="block mb-2 font-medium" htmlFor="backend">{t('backend')}</label>
        <select
          data-testid="storage-config-backend"
          id="backend"
          value={backend}
          onChange={e => { setBackend(e.target.value as BackendKind); resetSuccess(); }}
          className="p-2 border rounded w-full"
          disabled={loading}
        >
          <option value="local">{t('local')}</option>
          <option value="google_drive">{t('gdrive')}</option>
        </select>
      </div>

      {backend === "google_drive" && (
        <>
          <div>
            <Input
              label={t('folderId')}
              value={gdriveFolderId}
              onChange={e => { setGdriveFolderId(e.target.value); resetSuccess(); if (validationErrors.folder) setValidationErrors(v => ({ ...v, folder: undefined })); }}
              required
              disabled={loading}
              className="mb-1"
              data-testid="storage-config-gdrive-folder"
            />
            {validationErrors.folder && <p className="text-sm text-red-600 mb-2" role="alert">{validationErrors.folder}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('jsonPath')}</label>
            <div className="flex gap-2 items-start mb-1">
              <input
                type={showJsonPath ? "text" : "password"}
                value={gdriveJsonPath}
                onChange={e => { setGdriveJsonPath(e.target.value); resetSuccess(); if (validationErrors.json) setValidationErrors(v => ({ ...v, json: undefined })); }}
                disabled={loading}
                className="flex-1 p-2 border rounded"
                required
                data-testid="storage-config-gdrive-json"
              />
              <Button
                type="button"
                onClick={() => setShowJsonPath(s => !s)}
                disabled={loading}
                className="bg-gray-100 text-gray-700 hover:bg-gray-200"
              >
                {showJsonPath ? t('hide') : t('show')}
              </Button>
            </div>
            {validationErrors.json && <p className="text-sm text-red-600 mb-2" role="alert">{validationErrors.json}</p>}
          </div>
        </>
      )}

      <Button type="submit" disabled={loading || (backend === "google_drive" && (!gdriveFolderId.trim() || !gdriveJsonPath.trim()))}>
        {loading ? t('saving') : t('save')}
      </Button>

  {error && <div className="text-red-600" role="alert">{t('error')} : {error}</div>}
  {success && <div className="text-green-600" role="status">{t('saved')}</div>}

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
        data-testid="storage-config-toast"
        className={`relative rounded-md px-4 py-3 pr-10 shadow-lg text-sm font-medium ${toast.kind === "success" ? "bg-green-600 text-white" : "bg-red-600 text-white"}`}
      >
        <Toast.Title className="font-semibold text-base">{toast.title}</Toast.Title>
        {toast.description && <Toast.Description className="mt-1 opacity-90">{toast.description}</Toast.Description>}
        <Toast.Close className="absolute right-2 top-2 text-white/80 hover:text-white" aria-label="Fermer">×</Toast.Close>
      </Toast.Root>
    </form>
  );
}
