'use client';

import { Navigation } from '@/components/Navigation';

export default function CompaniesPage() {
  return (
    <Navigation>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Compagnies d&apos;assurance
          </h1>
          <p className="mt-2 text-gray-600">
            Gestion des compagnies d&apos;assurance et de leurs informations
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500">
            Page de gestion des compagnies d&apos;assurance en cours de développement...
          </p>
        </div>
      </div>
    </Navigation>
  );
}
