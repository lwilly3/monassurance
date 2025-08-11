import { useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export default function StorageConfigPage() {
  const [backend, setBackend] = useState<string>("local");
  const [gdriveFolderId, setGdriveFolderId] = useState("");
  const [gdriveJsonPath, setGdriveJsonPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const res = await fetch("/api/v1/admin/storage-config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          backend,
          gdrive_folder_id: backend === "google_drive" ? gdriveFolderId : undefined,
          gdrive_service_account_json_path: backend === "google_drive" ? gdriveJsonPath : undefined,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setSuccess(true);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="max-w-lg mx-auto mt-8 p-6 bg-white rounded shadow" onSubmit={handleSubmit}>
      <h2 className="text-xl font-bold mb-4">Configuration du stockage</h2>
      <label className="block mb-2 font-medium">Backend</label>
      <select value={backend} onChange={e => setBackend(e.target.value)} className="mb-4 p-2 border rounded">
        <option value="local">Local</option>
        <option value="google_drive">Google Drive</option>
      </select>
      {backend === "google_drive" && (
        <>
          <Input label="ID du dossier Google Drive" value={gdriveFolderId} onChange={e => setGdriveFolderId(e.target.value)} required className="mb-4" />
          <Input label="Chemin du fichier Service Account JSON" value={gdriveJsonPath} onChange={e => setGdriveJsonPath(e.target.value)} required className="mb-4" />
        </>
      )}
      <Button type="submit" disabled={loading}>{loading ? "Enregistrement..." : "Enregistrer"}</Button>
      {error && <div className="mt-2 text-red-600">Erreur : {error}</div>}
      {success && <div className="mt-2 text-green-600">Configuration enregistrée !</div>}
    </form>
  );
}
