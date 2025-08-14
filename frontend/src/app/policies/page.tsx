"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Table, Th, Td } from "@/components/ui/Table";
import { LoadingSpinner } from "@/components/ui/Loader";
import { Badge } from "@/components/ui/Badge";
import { Navigation } from "@/components/Navigation";

interface Policy {
  id: number;
  policy_number: string;
  client_id: number;
  client_name: string;
  company_id?: number;
  company_name?: string;
  product_name: string;
  premium_amount: number;
  effective_date: string;
  expiry_date: string;
  created_at: string;
}

function PoliciesPageContent() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredPolicies, setFilteredPolicies] = useState<Policy[]>([]);

  useEffect(() => {
    // Simuler le chargement des polices
    setTimeout(() => {
      const mockPolicies: Policy[] = [
        {
          id: 1,
          policy_number: "POL-2024-001",
          client_id: 1,
          client_name: "Jean Dupont",
          company_id: 1,
          company_name: "AXA France",
          product_name: "Assurance Auto Premium",
          premium_amount: 1200.50,
          effective_date: "2024-01-01T00:00:00Z",
          expiry_date: "2024-12-31T23:59:59Z",
          created_at: "2024-01-15T10:30:00Z",
        },
        {
          id: 2,
          policy_number: "POL-2024-002",
          client_id: 2,
          client_name: "Marie Martin",
          company_id: 2,
          company_name: "Allianz France",
          product_name: "Assurance Habitation",
          premium_amount: 850.00,
          effective_date: "2024-02-01T00:00:00Z",
          expiry_date: "2025-01-31T23:59:59Z",
          created_at: "2024-02-20T14:45:00Z",
        },
        {
          id: 3,
          policy_number: "POL-2024-003",
          client_id: 3,
          client_name: "Pierre Durand",
          company_id: 1,
          company_name: "AXA France",
          product_name: "Assurance Vie",
          premium_amount: 2400.00,
          effective_date: "2024-03-01T00:00:00Z",
          expiry_date: "2054-02-28T23:59:59Z",
          created_at: "2024-03-10T09:15:00Z",
        },
        {
          id: 4,
          policy_number: "POL-2024-004",
          client_id: 1,
          client_name: "Jean Dupont",
          company_id: 3,
          company_name: "Generali France",
          product_name: "Assurance Santé",
          premium_amount: 1800.75,
          effective_date: "2024-04-01T00:00:00Z",
          expiry_date: "2025-03-31T23:59:59Z",
          created_at: "2024-04-05T16:20:00Z",
        },
      ];
      setPolicies(mockPolicies);
      setFilteredPolicies(mockPolicies);
      setLoading(false);
    }, 800);
  }, []);

  useEffect(() => {
    const filtered = policies.filter(
      (policy) =>
        policy.policy_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        policy.client_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        policy.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        policy.company_name?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredPolicies(filtered);
  }, [searchTerm, policies]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("fr-FR");
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("fr-FR", {
      style: "currency",
      currency: "EUR",
    }).format(amount);
  };

  const isExpiringSoon = (expiryDate: string) => {
    const expiry = new Date(expiryDate);
    const now = new Date();
    const thirtyDaysFromNow = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000);
    return expiry <= thirtyDaysFromNow && expiry > now;
  };

  const isExpired = (expiryDate: string) => {
    return new Date(expiryDate) < new Date();
  };

  if (loading) {
    return <LoadingSpinner text="Chargement des polices..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Polices d&apos;assurance</h1>
          <p className="text-gray-600">Gérez les polices de vos clients</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          + Nouvelle police
        </Button>
      </div>

      {/* Search and Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>Liste des polices</CardTitle>
              <CardDescription>
                {filteredPolicies.length} police(s) trouvée(s)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Input
                  placeholder="Rechercher une police..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>

              <div className="overflow-x-auto">
                <Table>
                  <thead>
                    <tr className="border-b">
                      <Th>N° Police</Th>
                      <Th>Client</Th>
                      <Th>Produit</Th>
                      <Th>Compagnie</Th>
                      <Th>Prime</Th>
                      <Th>Expiration</Th>
                      <Th>Statut</Th>
                      <Th>Actions</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPolicies.map((policy) => (
                      <tr key={policy.id} className="border-b hover:bg-gray-50">
                        <Td>
                          <div className="font-medium">{policy.policy_number}</div>
                        </Td>
                        <Td>
                          <div className="font-medium">{policy.client_name}</div>
                        </Td>
                        <Td>
                          <div>{policy.product_name}</div>
                        </Td>
                        <Td>
                          <div className="text-sm">{policy.company_name || "-"}</div>
                        </Td>
                        <Td>
                          <div className="font-medium">
                            {formatCurrency(policy.premium_amount)}
                          </div>
                        </Td>
                        <Td>
                          <div>{formatDate(policy.expiry_date)}</div>
                        </Td>
                        <Td>
                          {isExpired(policy.expiry_date) ? (
                            <Badge variant="destructive">Expirée</Badge>
                          ) : isExpiringSoon(policy.expiry_date) ? (
                            <Badge variant="warning">Expire bientôt</Badge>
                          ) : (
                            <Badge variant="success">Active</Badge>
                          )}
                        </Td>
                        <Td>
                          <div className="flex space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-blue-600 hover:text-blue-700"
                            >
                              Voir
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-gray-600 hover:text-gray-700"
                            >
                              Modifier
                            </Button>
                          </div>
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Statistics */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Total Polices</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{policies.length}</div>
              <p className="text-xs text-gray-500">Polices actives</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Primes totales</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(
                  policies.reduce((sum, policy) => sum + policy.premium_amount, 0)
                )}
              </div>
              <p className="text-xs text-gray-500">
                <Badge variant="success">+15%</Badge> vs mois dernier
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Expirations proches</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {policies.filter((policy) => isExpiringSoon(policy.expiry_date)).length}
              </div>
              <p className="text-xs text-gray-500">
                <Badge variant="warning">Attention requise</Badge>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Répartition par produit</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span>Assurance Auto</span>
                <Badge variant="secondary">1 police</Badge>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span>Assurance Habitation</span>
                <Badge variant="secondary">1 police</Badge>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span>Assurance Vie</span>
                <Badge variant="secondary">1 police</Badge>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span>Assurance Santé</span>
                <Badge variant="secondary">1 police</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Actions rapides</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                📊 Rapport mensuel
              </Button>
              <Button variant="outline" className="w-full justify-start">
                📧 Relances expiration
              </Button>
              <Button variant="outline" className="w-full justify-start">
                📤 Exporter polices
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function PoliciesPage() {
  return (
    <Navigation>
      <PoliciesPageContent />
    </Navigation>
  );
}
