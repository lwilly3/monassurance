"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Table, Th, Td } from "@/components/ui/Table";
import { LoadingSpinner } from "@/components/ui/Loader";
import { Badge } from "@/components/ui/Badge";
import { Navigation } from "@/components/Navigation";

interface Client {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  address?: string;
  birth_date?: string;
  created_at: string;
}

function ClientsPageContent() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredClients, setFilteredClients] = useState<Client[]>([]);

  useEffect(() => {
    // Simuler le chargement des clients
    setTimeout(() => {
      const mockClients: Client[] = [
        {
          id: 1,
          first_name: "Jean",
          last_name: "Dupont",
          email: "jean.dupont@email.com",
          phone: "01 23 45 67 89",
          address: "123 Rue de la Paix, 75001 Paris",
          birth_date: "1980-05-15",
          created_at: "2024-01-15T10:30:00Z",
        },
        {
          id: 2,
          first_name: "Marie",
          last_name: "Martin",
          email: "marie.martin@email.com",
          phone: "01 98 76 54 32",
          address: "456 Avenue des Champs, 75008 Paris",
          birth_date: "1975-12-08",
          created_at: "2024-02-20T14:45:00Z",
        },
        {
          id: 3,
          first_name: "Pierre",
          last_name: "Durand",
          email: "pierre.durand@email.com",
          phone: "01 11 22 33 44",
          address: "789 Boulevard Saint-Germain, 75006 Paris",
          birth_date: "1990-08-22",
          created_at: "2024-03-10T09:15:00Z",
        },
      ];
      setClients(mockClients);
      setFilteredClients(mockClients);
      setLoading(false);
    }, 800);
  }, []);

  useEffect(() => {
    const filtered = clients.filter(
      (client) =>
        client.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.email.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredClients(filtered);
  }, [searchTerm, clients]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("fr-FR");
  };

  if (loading) {
    return <LoadingSpinner text="Chargement des clients..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Clients</h1>
          <p className="text-gray-600">Gérez vos clients et leurs informations</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          + Nouveau client
        </Button>
      </div>

      {/* Search and Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>Liste des clients</CardTitle>
              <CardDescription>
                {filteredClients.length} client(s) trouvé(s)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Input
                  placeholder="Rechercher un client..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>

              <div className="overflow-x-auto">
                <Table>
                  <thead>
                    <tr className="border-b">
                      <Th>Nom complet</Th>
                      <Th>Email</Th>
                      <Th>Téléphone</Th>
                      <Th>Date de naissance</Th>
                      <Th>Créé le</Th>
                      <Th>Actions</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredClients.map((client) => (
                      <tr key={client.id} className="border-b hover:bg-gray-50">
                        <Td>
                          <div>
                            <div className="font-medium">
                              {client.first_name} {client.last_name}
                            </div>
                            {client.address && (
                              <div className="text-sm text-gray-500">
                                {client.address}
                              </div>
                            )}
                          </div>
                        </Td>
                        <Td>{client.email}</Td>
                        <Td>{client.phone || "-"}</Td>
                        <Td>
                          {client.birth_date ? formatDate(client.birth_date) : "-"}
                        </Td>
                        <Td>{formatDate(client.created_at)}</Td>
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
              <CardTitle className="text-sm font-medium">Total Clients</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{clients.length}</div>
              <p className="text-xs text-gray-500">Tous les clients</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Nouveaux ce mois</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {clients.filter(
                  (client) =>
                    new Date(client.created_at).getMonth() === new Date().getMonth()
                ).length}
              </div>
              <p className="text-xs text-gray-500">
                <Badge variant="success">+20%</Badge> vs mois dernier
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Actions rapides</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                📧 Envoyer email groupé
              </Button>
              <Button variant="outline" className="w-full justify-start">
                📊 Exporter la liste
              </Button>
              <Button variant="outline" className="w-full justify-start">
                🏷️ Gérer les étiquettes
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function ClientsPage() {
  return (
    <Navigation>
      <ClientsPageContent />
    </Navigation>
  );
}