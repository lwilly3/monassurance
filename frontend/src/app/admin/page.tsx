'use client';

import { useState } from 'react';
import { Navigation } from '@/components/Navigation';
import { Card } from '@/components/ui/Card';
import { DataSeeder } from '@/components/admin/DataSeeder';

interface SeedStatus {
  has_data: boolean;
  companies_count: number;
  clients_count: number;
  policies_count: number;
  message: string;
}

export default function AdminPage() {
  const [seedStatus, setSeedStatus] = useState<SeedStatus | null>(null);

  return (
    <Navigation>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Administration
          </h1>
          <p className="mt-2 text-gray-600">
            Configuration et gestion de l&apos;application MonAssurance
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Gestion des données */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Gestion des données
            </h2>
            <DataSeeder onStatusChange={setSeedStatus} />
          </div>

          {/* Informations système */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Informations système
            </h2>
            <Card className="p-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">
                    Version de l&apos;application
                  </span>
                  <span className="text-sm text-gray-600">
                    1.0.0
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">
                    Base de données
                  </span>
                  <span className="text-sm text-gray-600">
                    PostgreSQL
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-700">
                    Environnement
                  </span>
                  <span className="text-sm text-gray-600">
                    Développement
                  </span>
                </div>

                {seedStatus && (
                  <div className="pt-4 border-t border-gray-200">
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      État des données
                    </div>
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Compagnies:</span>
                        <span className="text-gray-700">{seedStatus.companies_count}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Clients:</span>
                        <span className="text-gray-700">{seedStatus.clients_count}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Polices:</span>
                        <span className="text-gray-700">{seedStatus.policies_count}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>

        {/* Guide de démarrage */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Guide de démarrage
          </h2>
          <Card className="p-6">
            <div className="prose prose-sm max-w-none">
              <h3 className="text-lg font-medium text-gray-900 mb-3">
                Configuration initiale
              </h3>
              
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">1</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Choisir le mode de données</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Pour le développement et les tests, utilisez les données de remplissage.
                      Pour la production, commencez avec une base vide.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">2</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Configurer le stockage</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Configurez votre méthode de stockage préférée (local, Google Drive, ou S3)
                      dans les paramètres de l&apos;application.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-blue-600">3</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900">Commencer à utiliser</h4>
                    <p className="text-sm text-gray-600 mt-1">
                      Naviguez vers les sections Clients, Compagnies ou Polices pour commencer
                      à gérer vos données d&apos;assurance.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </Navigation>
  );
}
