"use client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LoadingSpinner } from "@/components/ui/Loader";
import { useState, useEffect } from "react";

interface DashboardStats {
  totalClients: number;
  totalCompanies: number;
  totalPolicies: number;
  totalDocuments: number;
  recentActivities: Activity[];
}

interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  status: "success" | "warning" | "error";
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simuler le chargement des données
    setTimeout(() => {
      setStats({
        totalClients: 1234,
        totalCompanies: 45,
        totalPolicies: 2856,
        totalDocuments: 8942,
        recentActivities: [
          {
            id: "1",
            type: "Nouveau client",
            description: "Ajout du client Jean Dupont",
            timestamp: "Il y a 2 heures",
            status: "success",
          },
          {
            id: "2",
            type: "Police modifiée",
            description: "Modification de la police P-2024-001",
            timestamp: "Il y a 4 heures",
            status: "warning",
          },
          {
            id: "3",
            type: "Document généré",
            description: "Génération du rapport mensuel",
            timestamp: "Il y a 6 heures",
            status: "success",
          },
          {
            id: "4",
            type: "Erreur système",
            description: "Échec de synchronisation avec la compagnie ABC",
            timestamp: "Il y a 8 heures",
            status: "error",
          },
        ],
      });
      setLoading(false);
    }, 1000);
  }, []);

  if (loading) {
    return <LoadingSpinner text="Chargement du tableau de bord..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="text-gray-600">Aperçu de votre activité MonAssurance</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Clients</CardTitle>
            <span className="text-2xl">👥</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalClients.toLocaleString()}</div>
            <p className="text-xs text-gray-500">+12% ce mois</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compagnies</CardTitle>
            <span className="text-2xl">🏢</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalCompanies}</div>
            <p className="text-xs text-gray-500">+2 nouvelles</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Polices Actives</CardTitle>
            <span className="text-2xl">📋</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalPolicies.toLocaleString()}</div>
            <p className="text-xs text-gray-500">+8% ce mois</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <span className="text-2xl">🗂️</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.totalDocuments.toLocaleString()}</div>
            <p className="text-xs text-gray-500">+145 cette semaine</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Activités récentes</CardTitle>
            <CardDescription>Dernières actions dans le système</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {stats?.recentActivities.map((activity) => (
              <div key={activity.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-sm">{activity.type}</span>
                    <Badge
                      variant={
                        activity.status === "success"
                          ? "success"
                          : activity.status === "error"
                          ? "destructive"
                          : "warning"
                      }
                    >
                      {activity.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                  <p className="text-xs text-gray-400 mt-1">{activity.timestamp}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions rapides</CardTitle>
            <CardDescription>Raccourcis vers les tâches courantes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <QuickActionButton
              icon="👤"
              title="Nouveau client"
              description="Ajouter un nouveau client"
              href="/clients/new"
            />
            <QuickActionButton
              icon="📋"
              title="Nouvelle police"
              description="Créer une nouvelle police d'assurance"
              href="/policies/new"
            />
            <QuickActionButton
              icon="📄"
              title="Générer un document"
              description="Créer un document à partir d'un template"
              href="/documents/new"
            />
            <QuickActionButton
              icon="📈"
              title="Voir les rapports"
              description="Consulter les rapports et statistiques"
              href="/reports"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface QuickActionButtonProps {
  icon: string;
  title: string;
  description: string;
  href: string;
}

function QuickActionButton({ icon, title, description, href }: QuickActionButtonProps) {
  return (
    <a
      href={href}
      className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
    >
      <span className="text-2xl mr-3">{icon}</span>
      <div>
        <h4 className="font-medium text-sm">{title}</h4>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
    </a>
  );
}
