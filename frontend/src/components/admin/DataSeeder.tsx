'use client';

import { useState, useCallback } from 'react';
import * as React from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Loader } from '@/components/ui/Loader';

interface SeedStatus {
  has_data: boolean;
  companies_count: number;
  clients_count: number;
  policies_count: number;
  message: string;
}

interface SeedActionResponse {
  success: boolean;
  message: string;
  data?: SeedStatus;
}

interface DataSeederProps {
  onStatusChange?: (status: SeedStatus) => void;
}

export function DataSeeder({ onStatusChange }: DataSeederProps) {
  const [status, setStatus] = useState<SeedStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setError(null);
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setError('Aucun token d\'authentification trouvé. Veuillez vous reconnecter.');
        return;
      }
      
      const response = await fetch('/api/v1/seed/status', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          setError('Token d\'authentification invalide. Veuillez vous reconnecter.');
        } else if (response.status === 404) {
          setError('API de gestion des données non disponible.');
        } else {
          setError(`Erreur du serveur: ${response.status}`);
        }
        return;
      }
      
      const data: SeedStatus = await response.json();
      setStatus(data);
      onStatusChange?.(data);
    } catch (err) {
      if (err instanceof TypeError && err.message.includes('fetch')) {
        setError('Impossible de se connecter au serveur. Vérifiez que le backend est démarré.');
      } else {
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      }
    }
  }, [onStatusChange]);

  const handleAction = async (action: 'populate' | 'clear') => {
    try {
      setLoading(true);
      setError(null);
      
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        setError('Aucun token d\'authentification trouvé. Veuillez vous reconnecter.');
        return;
      }
      
      const response = await fetch(`/api/v1/seed/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          setError('Token d\'authentification invalide. Veuillez vous reconnecter.');
        } else if (response.status === 404) {
          setError('API de gestion des données non disponible.');
        } else {
          setError(`Erreur du serveur: ${response.status}`);
        }
        return;
      }
      
      const result: SeedActionResponse = await response.json();
      
      if (result.success && result.data) {
        setStatus(result.data);
        onStatusChange?.(result.data);
      } else {
        setError(result.message);
      }
    } catch (err) {
      if (err instanceof TypeError && err.message.includes('fetch')) {
        setError('Impossible de se connecter au serveur. Vérifiez que le backend est démarré.');
      } else {
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      }
    } finally {
      setLoading(false);
    }
  };

  // Charger le statut au montage
  React.useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Données de remplissage
        </h3>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchStatus}
          disabled={loading}
        >
          Actualiser
        </Button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">
                Erreur de connexion
              </h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              {error.includes('serveur') && (
                <div className="mt-2 text-sm text-red-600">
                  <p className="font-medium">Solutions possibles :</p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>Vérifiez que le serveur backend est démarré sur le port 8000</li>
                    <li>Actualisez la page après le démarrage du serveur</li>
                    <li>Vérifiez votre connexion réseau</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {status && (
        <div className="space-y-4">
          {/* Statut actuel */}
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="text-sm font-medium text-gray-700">
                Statut de la base de données
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {status.message}
              </p>
            </div>
            <Badge variant={status.has_data ? 'success' : 'warning'}>
              {status.has_data ? 'Données présentes' : 'Base vide'}
            </Badge>
          </div>

          {/* Statistiques */}
          {status.has_data && (
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {status.companies_count}
                </div>
                <div className="text-xs text-blue-500">Compagnies</div>
              </div>
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {status.clients_count}
                </div>
                <div className="text-xs text-green-500">Clients</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {status.policies_count}
                </div>
                <div className="text-xs text-purple-500">Polices</div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-3">
            {!status.has_data ? (
              <div className="space-y-3">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-medium text-blue-900 mb-2">
                    Remplir avec des données de test
                  </h4>
                  <p className="text-sm text-blue-700 mb-3">
                    Ajoute des exemples de compagnies, clients et polices pour tester l&apos;application.
                    Parfait pour le développement et les démonstrations.
                  </p>
                  <Button
                    onClick={() => handleAction('populate')}
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? <Loader size="sm" /> : null}
                    Remplir la base de données
                  </Button>
                </div>
                <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">
                    Commencer avec une base vide
                  </h4>
                  <p className="text-sm text-gray-600">
                    Recommandé pour la production. Vous pourrez ajouter vos propres données
                    via l&apos;interface d&apos;administration.
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                <h4 className="font-medium text-orange-900 mb-2">
                  Vider la base de données
                </h4>
                <p className="text-sm text-orange-700 mb-3">
                  ⚠️ Cette action supprimera toutes les données de test (compagnies, clients, polices).
                  Les utilisateurs et la configuration seront conservés.
                </p>
                <Button
                  variant="danger"
                  onClick={() => handleAction('clear')}
                  disabled={loading}
                  className="w-full"
                >
                  {loading ? <Loader size="sm" /> : null}
                  Vider la base de données
                </Button>
              </div>
            )}
          </div>
        </div>
      )}

      {!status && !error && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}
    </Card>
  );
}
