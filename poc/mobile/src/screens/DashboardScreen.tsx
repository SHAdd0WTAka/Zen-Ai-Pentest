/**
 * Dashboard Screen for Mobile App
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { Card, Title, Paragraph, Badge } from 'react-native-paper';
import { useQuery } from '@tanstack/react-query';
import { LineChart, PieChart } from 'react-native-chart-kit';

import { api } from '../api/client';
import { theme } from '../theme';

export const DashboardScreen: React.FC = () => {
  const { data: stats, isLoading, refetch } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats');
      return response.data;
    },
  });

  const vulnerabilityData = stats ? [
    {
      name: 'Critical',
      population: stats.criticalVulnerabilities,
      color: '#dc2626',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
    {
      name: 'High',
      population: stats.highVulnerabilities,
      color: '#ea580c',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
    {
      name: 'Medium',
      population: stats.mediumVulnerabilities,
      color: '#ca8a04',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
    {
      name: 'Low',
      population: stats.lowVulnerabilities,
      color: '#16a34a',
      legendFontColor: '#7F7F7F',
      legendFontSize: 12,
    },
  ] : [];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={refetch} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome back!</Text>
        <Text style={styles.subtitle}>Here's your security overview</Text>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsGrid}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={styles.statNumber}>{stats?.totalScans || 0}</Title>
            <Paragraph>Total Scans</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={[styles.statNumber, styles.criticalText]}>
              {stats?.criticalVulnerabilities || 0}
            </Title>
            <Paragraph>Critical</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={styles.statNumber}>
              {stats?.totalVulnerabilities || 0}
            </Title>
            <Paragraph>Total Vulns</Paragraph>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Title style={styles.statNumber}>
              {stats?.onlineAgents || 0}
            </Title>
            <Paragraph>Agents Online</Paragraph>
          </Card.Content>
        </Card>
      </View>

      {/* Vulnerability Chart */}
      <Card style={styles.chartCard}>
        <Card.Content>
          <Title>Vulnerability Distribution</Title>
          {vulnerabilityData.length > 0 && (
            <PieChart
              data={vulnerabilityData}
              width={350}
              height={200}
              chartConfig={{
                color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
              }}
              accessor="population"
              backgroundColor="transparent"
              paddingLeft="15"
            />
          )}
        </Card.Content>
      </Card>

      {/* Recent Scans */}
      <Card style={styles.listCard}>
        <Card.Content>
          <Title>Recent Scans</Title>
          {stats?.recentScans?.map((scan: any) => (
            <View key={scan.id} style={styles.scanItem}>
              <View style={styles.scanHeader}>
                <Text style={styles.scanName}>{scan.name}</Text>
                <Badge
                  style={[
                    styles.statusBadge,
                    { backgroundColor: getStatusColor(scan.status) },
                  ]}
                >
                  {scan.status}
                </Badge>
              </View>
              <Text style={styles.scanTarget}>{scan.target}</Text>
              <Text style={styles.scanFindings}>
                {scan.findings} findings • {scan.progress}% complete
              </Text>
            </View>
          ))}
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: '#6b7280',
    running: '#0ea5e9',
    completed: '#16a34a',
    failed: '#dc2626',
  };
  return colors[status] || '#6b7280';
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#0f172a',
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  subtitle: {
    fontSize: 16,
    color: '#94a3b8',
    marginTop: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 10,
    gap: 10,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    margin: 5,
  },
  statNumber: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  criticalText: {
    color: '#dc2626',
  },
  chartCard: {
    margin: 10,
  },
  listCard: {
    margin: 10,
    marginBottom: 20,
  },
  scanItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  scanHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  scanName: {
    fontSize: 16,
    fontWeight: '600',
  },
  scanTarget: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  scanFindings: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
  statusBadge: {
    alignSelf: 'flex-start',
  },
});
