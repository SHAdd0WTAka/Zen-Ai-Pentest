// ============================================
// Zen-AI-Pentest Platform - Compliance Page
// ============================================

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ClipboardCheck,
  Shield,
  FileText,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Loader2,
  Play,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { complianceApi, dashboardApi } from '@/services/api';
import { ComplianceScoreChart } from '@/components/charts/DashboardCharts';

// ============================================
// Framework Card Component
// ============================================
interface Framework {
  id: string;
  name: string;
  description: string;
  version: string;
  controls: any[];
}

function FrameworkCard({ framework }: { framework: Framework }) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
            <Shield className="w-6 h-6 text-primary" />
          </div>
          <Badge variant="outline">v{framework.version}</Badge>
        </div>
        <CardTitle className="mt-4">{framework.name}</CardTitle>
        <CardDescription>{framework.description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {framework.controls.length} controls
          </span>
          <Button size="sm" variant="outline">
            <Play className="w-4 h-4 mr-2" />
            Run Assessment
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ============================================
// Main Compliance Page
// ============================================
export function CompliancePage() {
  const [activeTab, setActiveTab] = useState('overview');

  const { data: frameworks, isLoading } = useQuery({
    queryKey: ['compliance-frameworks'],
    queryFn: () => complianceApi.getFrameworks(),
  });

  const { data: complianceScore } = useQuery({
    queryKey: ['compliance-score'],
    queryFn: () => dashboardApi.getComplianceScore(),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Compliance</h1>
          <p className="text-muted-foreground">
            Monitor and maintain compliance with security standards
          </p>
        </div>
        <Button>
          <Play className="w-4 h-4 mr-2" />
          Run Assessment
        </Button>
      </div>

      {/* Overall Score */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Overall Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="w-16 h-16 rounded-full border-4 border-primary flex items-center justify-center">
                <span className="text-2xl font-bold">{complianceScore?.overall || 0}%</span>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">
                  {complianceScore?.overall && complianceScore.overall >= 80
                    ? 'Excellent'
                    : complianceScore?.overall && complianceScore.overall >= 60
                    ? 'Good'
                    : 'Needs Improvement'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Passed Controls
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="text-2xl font-bold">--</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Failed Controls
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-500" />
              <span className="text-2xl font-bold">--</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Partial Controls
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500" />
              <span className="text-2xl font-bold">--</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="frameworks">Frameworks</TabsTrigger>
          <TabsTrigger value="assessments">Assessments</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Compliance by Framework</CardTitle>
              <CardDescription>Compliance scores across different frameworks</CardDescription>
            </CardHeader>
            <CardContent>
              <ComplianceScoreChart />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Assessments</CardTitle>
              <CardDescription>Latest compliance assessment results</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <ClipboardCheck className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No assessments yet</p>
                <Button className="mt-4">
                  <Play className="w-4 h-4 mr-2" />
                  Run First Assessment
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="frameworks" className="space-y-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
          ) : frameworks && frameworks.length > 0 ? (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {frameworks.map((framework) => (
                <FrameworkCard key={framework.id} framework={framework} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No frameworks available</p>
            </div>
          )}
        </TabsContent>

        <TabsContent value="assessments">
          <Card>
            <CardHeader>
              <CardTitle>Assessment History</CardTitle>
              <CardDescription>View past compliance assessments</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No assessments yet</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
