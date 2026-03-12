// ============================================
// Zen-AI-Pentest Platform - Network Graph Page
// Full Network Topology Visualization
// ============================================

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import * as d3 from 'd3';
import {
  Network,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Download,
  RefreshCw,
  Search,
  Shield,
  AlertTriangle,
  Server,
  Laptop,
  Smartphone,
  Router,
  Activity,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { toast } from 'sonner';
import { dashboardApi } from '@/services/api';

// ============================================
// Types - Using types from @/types
// ============================================
import type { NetworkNode, NetworkEdge } from '@/types';

interface NetworkData {
  nodes: NetworkNode[];
  links: NetworkEdge[];
}

// ============================================
// Helper Functions
// ============================================
const getNodeIcon = (type: string) => {
  switch (type) {
    case 'server':
      return Server;
    case 'workstation':
      return Laptop;
    case 'mobile':
      return Smartphone;
    case 'router':
      return Router;
    case 'firewall':
      return Shield;
    default:
      return Activity;
  }
};

const getNodeColor = (status: string) => {
  switch (status) {
    case 'online':
      return '#22c55e';
    case 'offline':
      return '#6b7280';
    case 'warning':
      return '#f59e0b';
    case 'compromised':
      return '#ef4444';
    default:
      return '#6b7280';
  }
};

const getLinkColor = (status: string) => {
  switch (status) {
    case 'active':
      return '#22c55e';
    case 'inactive':
      return '#6b7280';
    case 'suspicious':
      return '#f59e0b';
    default:
      return '#6b7280';
  }
};

// ============================================
// Main Component
// ============================================
export function NetworkGraphPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showVulnerabilities, setShowVulnerabilities] = useState(true);
  const [showOffline, setShowOffline] = useState(true);
  const [nodeSize, setNodeSize] = useState(30);
  const [filterType, setFilterType] = useState<string>('all');

  const { data: networkData, isLoading, refetch } = useQuery({
    queryKey: ['network-topology'],
    queryFn: dashboardApi.getNetworkGraph,
  });

  // Filter nodes based on search and filters
  const filteredData = networkData
    ? {
        nodes: networkData.nodes.filter((node: any) => {
          const matchesSearch =
            searchQuery === '' ||
            (node.name && node.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
            (node.ip && node.ip.includes(searchQuery));
          const matchesType = filterType === 'all' || node.type === filterType;
          const matchesOffline = showOffline || node.status !== 'offline';
          return matchesSearch && matchesType && matchesOffline;
        }),
        links: networkData.links.filter((link: any) => {
          const sourceId = typeof link.source === 'string' ? link.source : link.source?.id;
          const targetId = typeof link.target === 'string' ? link.target : link.target?.id;
          const sourceExists = networkData.nodes.find((n: any) => n.id === sourceId);
          const targetExists = networkData.nodes.find((n: any) => n.id === targetId);
          return sourceExists && targetExists;
        }),
      }
    : { nodes: [], links: [] };

  // D3 Force Simulation
  useEffect(() => {
    if (!svgRef.current || !containerRef.current || filteredData.nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg.selectAll('*').remove();

    // Create zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoomLevel(event.transform.k);
      });

    svg.call(zoom);

    const g = svg.append('g');

    // Create force simulation
    const simulation = d3
      .forceSimulation<NetworkNode>(filteredData.nodes)
      .force(
        'link',
        d3
          .forceLink<NetworkNode, NetworkEdge>(filteredData.links)
          .id((d: any) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(nodeSize + 10));

    // Create links
    const link = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(filteredData.links)
      .enter()
      .append('line')
      .attr('stroke', (d: any) => getLinkColor(d.status || 'active'))
      .attr('stroke-width', (d: any) => Math.sqrt((d.bandwidth || 100) / 100) + 1)
      .attr('stroke-opacity', 0.6);

    // Create nodes group
    const node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(filteredData.nodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .call(
        d3
          .drag<SVGGElement, NetworkNode>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      )
      .on('click', (event: any, d: NetworkNode) => {
        event.stopPropagation();
        setSelectedNode(d);
      });

    // Add node circles
    node
      .append('circle')
      .attr('r', nodeSize)
      .attr('fill', (d) => getNodeColor(d.status))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('class', 'transition-all duration-200 hover:brightness-110');

    // Add vulnerability indicator
    if (showVulnerabilities) {
      node
        .filter((d: any) => (d.vulnerabilities || 0) > 0)
        .append('circle')
        .attr('r', 8)
        .attr('cx', nodeSize * 0.7)
        .attr('cy', -nodeSize * 0.7)
        .attr('fill', '#ef4444')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1);

      node
        .filter((d: any) => (d.vulnerabilities || 0) > 0)
        .append('text')
        .attr('x', nodeSize * 0.7)
        .attr('y', -nodeSize * 0.7 + 3)
        .attr('text-anchor', 'middle')
        .attr('fill', '#fff')
        .attr('font-size', '10px')
        .attr('font-weight', 'bold')
        .text((d: any) => (d.vulnerabilities > 9 ? '9+' : d.vulnerabilities));
    }

    // Add node labels
    node
      .append('text')
      .attr('dy', nodeSize + 15)
      .attr('text-anchor', 'middle')
      .attr('fill', 'currentColor')
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .text((d: any) => d.name || d.label || d.id);

    // Add IP labels
    node
      .append('text')
      .attr('dy', nodeSize + 28)
      .attr('text-anchor', 'middle')
      .attr('fill', '#6b7280')
      .attr('font-size', '10px')
      .text((d: any) => d.ip || '');

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (typeof d.source !== 'string' ? d.source.x || 0 : 0))
        .attr('y1', (d) => (typeof d.source !== 'string' ? d.source.y || 0 : 0))
        .attr('x2', (d) => (typeof d.target !== 'string' ? d.target.x || 0 : 0))
        .attr('y2', (d) => (typeof d.target !== 'string' ? d.target.y || 0 : 0));

      node.attr('transform', (d) => `translate(${d.x || 0},${d.y || 0})`);
    });

    // Click background to deselect
    svg.on('click', () => setSelectedNode(null));

    return () => {
      simulation.stop();
    };
  }, [filteredData, nodeSize, showVulnerabilities]);

  // Zoom controls
  const handleZoomIn = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call(
        (d3.zoom() as any).transform,
        d3.zoomTransform(svgRef.current).scale(zoomLevel * 1.2)
      );
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call(
        (d3.zoom() as any).transform,
        d3.zoomTransform(svgRef.current).scale(zoomLevel / 1.2)
      );
    }
  };

  const handleReset = () => {
    if (svgRef.current) {
      const svg = d3.select(svgRef.current);
      svg.transition().call((d3.zoom() as any).transform, d3.zoomIdentity);
    }
  };

  const handleExport = () => {
    toast.success('Network topology exported successfully');
  };

  // Stats
  const stats = networkData
    ? {
        total: networkData.nodes.length,
        online: networkData.nodes.filter((n: any) => n.status === 'online').length,
        offline: networkData.nodes.filter((n: any) => n.status === 'offline').length,
        compromised: networkData.nodes.filter((n: any) => n.status === 'compromised').length,
        vulnerabilities: networkData.nodes.reduce((acc: number, n: any) => acc + (n.vulnerabilities || 0), 0),
      }
    : { total: 0, online: 0, offline: 0, compromised: 0, vulnerabilities: 0 };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Network Topology</h1>
          <p className="text-muted-foreground">
            Visualize and explore your network infrastructure
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => refetch()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online</CardTitle>
            <Activity className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{stats.online}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline</CardTitle>
            <Server className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-500">{stats.offline}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Compromised</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{stats.compromised}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vulnerabilities</CardTitle>
            <Shield className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-500">{stats.vulnerabilities}</div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-4">
        {/* Graph */}
        <Card className="lg:col-span-3">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between">
              <CardTitle>Network Map</CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search devices..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-64 pl-8"
                  />
                </div>
                <Sheet>
                  <SheetTrigger asChild>
                    <Button variant="outline" size="icon">
                      <Filter className="h-4 w-4" />
                    </Button>
                  </SheetTrigger>
                  <SheetContent>
                    <SheetHeader>
                      <SheetTitle>Filter Options</SheetTitle>
                    </SheetHeader>
                    <div className="mt-6 space-y-6">
                      <div className="space-y-2">
                        <Label>Device Type</Label>
                        <Select value={filterType} onValueChange={setFilterType}>
                          <SelectTrigger>
                            <SelectValue placeholder="All types" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Types</SelectItem>
                            <SelectItem value="server">Servers</SelectItem>
                            <SelectItem value="workstation">Workstations</SelectItem>
                            <SelectItem value="mobile">Mobile Devices</SelectItem>
                            <SelectItem value="router">Routers</SelectItem>
                            <SelectItem value="firewall">Firewalls</SelectItem>
                            <SelectItem value="iot">IoT Devices</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Node Size</Label>
                        <Slider
                          value={[nodeSize]}
                          onValueChange={(value) => setNodeSize(value[0])}
                          min={20}
                          max={50}
                          step={5}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Show Vulnerabilities</Label>
                        <Switch checked={showVulnerabilities} onCheckedChange={setShowVulnerabilities} />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Show Offline Devices</Label>
                        <Switch checked={showOffline} onCheckedChange={setShowOffline} />
                      </div>
                    </div>
                  </SheetContent>
                </Sheet>
                <Button variant="outline" size="icon" onClick={handleZoomIn}>
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={handleZoomOut}>
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="icon" onClick={handleReset}>
                  <Maximize2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div ref={containerRef} className="relative h-[600px] w-full">
              {isLoading ? (
                <div className="flex h-full items-center justify-center">
                  <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <svg ref={svgRef} className="h-full w-full" />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Selected Node Details */}
          <Card>
            <CardHeader>
              <CardTitle>Device Details</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedNode ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div
                      className="flex h-10 w-10 items-center justify-center rounded-full"
                      style={{ backgroundColor: getNodeColor(selectedNode.status) }}
                    >
                      {(() => {
                        const Icon = getNodeIcon(selectedNode.type);
                        return <Icon className="h-5 w-5 text-white" />;
                      })()}
                    </div>
                    <div>
                      <p className="font-medium">{selectedNode.name}</p>
                      <Badge
                        variant={
                          selectedNode.status === 'online'
                            ? 'default'
                            : selectedNode.status === 'compromised'
                              ? 'destructive'
                            : 'secondary'
                        }
                      >
                        {selectedNode.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">IP Address</span>
                      <span>{selectedNode.ip}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Type</span>
                      <span className="capitalize">{selectedNode.type}</span>
                    </div>
                    {selectedNode.os && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">OS</span>
                        <span>{selectedNode.os}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Services</span>
                      <span>{selectedNode.services}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Vulnerabilities</span>
                      <span
                        className={
                          selectedNode.vulnerabilities > 0 ? 'text-red-500 font-medium' : ''
                        }
                      >
                        {selectedNode.vulnerabilities}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1">
                      <Search className="mr-2 h-4 w-4" />
                      Scan
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1">
                      <Activity className="mr-2 h-4 w-4" />
                      Monitor
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-center text-muted-foreground">
                  Click on a device to view details
                </p>
              )}
            </CardContent>
          </Card>

          {/* Legend */}
          <Card>
            <CardHeader>
              <CardTitle>Legend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-green-500" />
                  <span className="text-sm">Online</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-gray-500" />
                  <span className="text-sm">Offline</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-amber-500" />
                  <span className="text-sm">Warning</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-red-500" />
                  <span className="text-sm">Compromised</span>
                </div>
                <div className="border-t pt-3 mt-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    <span className="text-sm">Server</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Laptop className="h-4 w-4" />
                    <span className="text-sm">Workstation</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Smartphone className="h-4 w-4" />
                    <span className="text-sm">Mobile</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Router className="h-4 w-4" />
                    <span className="text-sm">Router</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    <span className="text-sm">Firewall</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    <span className="text-sm">IoT</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
