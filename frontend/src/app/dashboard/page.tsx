'use client';

import { Navigation } from '@/components/Navigation';

export default function DashboardPage() {
  return (
    <Navigation>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Tableau de bord
          </h1>
          <p className="mt-2 text-gray-600">
            Vue d&apos;ensemble de l&apos;activité et des métriques
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Statistiques</h3>
            <p className="text-gray-500">Métriques en cours de développement...</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Rapports</h3>
            <p className="text-gray-500">Génération de rapports en cours de développement...</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Activité récente</h3>
            <p className="text-gray-500">Suivi d&apos;activité en cours de développement...</p>
          </div>
        </div>
      </div>
    </Navigation>
  );
}
