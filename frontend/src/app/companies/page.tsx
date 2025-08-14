"use client";
import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Table, Th, Td } from "@/components/ui/Table";
import { LoadingSpinner } from "@/components/ui/Loader";
import { Badge } from "@/components/ui/Badge";
import { Navigation } from "@/components/Navigation";

interface Company {
  id: number;
  name: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  website?: string;
  created_at: string;
}

function CompaniesPageContent() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredCompanies, setFilteredCompanies] = useState<Company[]>([]);

  useEffect(() => {
    // Simuler le chargement des compagnies
    setTimeout(() => {
      const mockCompanies: Company[] = [
        {
          id: 1,
          name: "AXA France",
          contact_email: "contact@axa.fr",
          contact_phone: "01 40 14 91 00",
          address: "25 Avenue Matignon, 75008 Paris",
          website: "https://www.axa.fr",
          created_at: "2024-01-10T08:00:00Z",
        },
        {
          id: 2,
          name: "Allianz France",
          contact_email: "info@allianz.fr",
          contact_phone: "01 44 86 20 00",
          address: "87 Rue de Richelieu, 75002 Paris",
          website: "https://www.allianz.fr",
          created_at: "2024-01-15T10:30:00Z",
        },
        {
          id: 3,
          name: "Generali France",
          contact_email: "contact@generali.fr",
          contact_phone: "01 58 38 20 00",
          address: "2 Rue Pillet-Will, 75009 Paris",
          website: "https://www.generali.fr",
          created_at: "2024-02-01T14:15:00Z",
        },
        {
          id: 4,
          name: "MAIF",
          contact_email: "info@maif.fr",
          contact_phone: "05 49 73 73 73",
          address: "200 Avenue Salvador Allende, 79000 Niort",
          website: "https://www.maif.fr",
          created_at: "2024-02-10T09:45:00Z",
        },
      ];
      setCompanies(mockCompanies);
      setFilteredCompanies(mockCompanies);
      setLoading(false);
    }, 800);
  }, []);

  useEffect(() => {
    const filtered = companies.filter(
      (company) =>
        company.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        company.contact_email?.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredCompanies(filtered);
  }, [searchTerm, companies]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("fr-FR");
  };

  if (loading) {
    return <LoadingSpinner text="Chargement des compagnies..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compagnies d&apos;assurance</h1>
          <p className="text-gray-600">Gérez vos partenaires et compagnies d&apos;assurance</p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          + Nouvelle compagnie
        </Button>
      </div>

      {/* Search and Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>Liste des compagnies</CardTitle>
              <CardDescription>
                {filteredCompanies.length} compagnie(s) trouvée(s)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Input
                  placeholder="Rechercher une compagnie..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="max-w-sm"
                />
              </div>

              <div className="overflow-x-auto">
                <Table>
                  <thead>
                    <tr className="border-b">
                      <Th>Nom de la compagnie</Th>
                      <Th>Contact</Th>
                      <Th>Adresse</Th>
                      <Th>Site web</Th>
                      <Th>Créée le</Th>
                      <Th>Actions</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCompanies.map((company) => (
                      <tr key={company.id} className="border-b hover:bg-gray-50">
                        <Td>
                          <div className="font-medium">{company.name}</div>
                        </Td>
                        <Td>
                          <div>
                            {company.contact_email && (
                              <div className="text-sm">{company.contact_email}</div>
                            )}
                            {company.contact_phone && (
                              <div className="text-sm text-gray-500">{company.contact_phone}</div>
                            )}
                          </div>
                        </Td>
                        <Td>
                          <div className="text-sm">{company.address || "-"}</div>
                        </Td>
                        <Td>
                          {company.website ? (
                            <a
                              href={company.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 text-sm"
                            >
                              Visiter
                            </a>
                          ) : (
                            "-"
                          )}
                        </Td>
                        <Td>{formatDate(company.created_at)}</Td>
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
              <CardTitle className="text-sm font-medium">Total Compagnies</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{companies.length}</div>
              <p className="text-xs text-gray-500">Partenaires actifs</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Nouvelles ce mois</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {companies.filter(
                  (company) =>
                    new Date(company.created_at).getMonth() === new Date().getMonth()
                ).length}
              </div>
              <p className="text-xs text-gray-500">
                <Badge variant="success">Nouveaux partenariats</Badge>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Top compagnies</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex justify-between items-center text-sm">
                <span>AXA France</span>
                <Badge variant="secondary">156 polices</Badge>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span>Allianz France</span>
                <Badge variant="secondary">134 polices</Badge>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span>Generali France</span>
                <Badge variant="secondary">89 polices</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Actions rapides</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button variant="outline" className="w-full justify-start">
                📊 Rapport par compagnie
              </Button>
              <Button variant="outline" className="w-full justify-start">
                📧 Contacter toutes
              </Button>
              <Button variant="outline" className="w-full justify-start">
                📤 Exporter la liste
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function CompaniesPage() {
  return (
    <Navigation>
      <CompaniesPageContent />
    </Navigation>
  );
}
