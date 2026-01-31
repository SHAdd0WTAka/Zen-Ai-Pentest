// ============================================
// Attack Graph Visualization Component
// ============================================

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as d3 from 'd3';
import { AttackGraph as AttackGraphType, AttackNode, AttackEdge, NodeType } from '../../types';

interface AttackGraphProps {
  data: AttackGraphType;
  onNodeClick?: (node: AttackNode) => void;
  onEdgeClick?: (edge: AttackEdge) => void;
  selectedPath?: string[];
  width?: number;
  height?: number;
}

interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  type: NodeType;
  label: string;
  data: AttackNode['data'];
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  id: string;
  source: string | D3Node;
  target: string | D3Node;
  type: string;
  label?: string;
}

// Node colors by type
const nodeColors: Record<NodeType, string> = {
  host: '#3b82f6', // blue
  service: '#10b981', // emerald
  vulnerability: '#ef4444', // red
  credential: '#f59e0b', // amber
  data: '#8b5cf6', // violet
};

const nodeIcons: Record<NodeType, string> = {
  host: '🖥️',
  service: '⚙️',
  vulnerability: '🐛',
  credential: '🔑',
  data: '📁',
};

const AttackGraph: React.FC<AttackGraphProps> = ({
  data,
  onNodeClick,
  onEdgeClick,
  selectedPath,
  width = 800,
  height = 600,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<AttackNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Transform data for D3
  const nodes: D3Node[] = data.nodes.map((n) => ({ ...n }));
  const links: D3Link[] = data.edges.map((e) => ({ ...e }));

  // Export graph as PNG
  const exportPNG = useCallback(() => {
    if (!svgRef.current) return;
    
    const svgElement = svgRef.current;
    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    canvas.width = width;
    canvas.height = height;
    
    img.onload = () => {
      ctx?.drawImage(img, 0, 0);
      const pngFile = canvas.toDataURL('image/png');
      const downloadLink = document.createElement('a');
      downloadLink.download = `attack-graph-${Date.now()}.png`;
      downloadLink.href = pngFile;
      downloadLink.click();
    };
    
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  }, [width, height]);

  // Export graph as SVG
  const exportSVG = useCallback(() => {
    if (!svgRef.current) return;
    
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `attack-graph-${Date.now()}.svg`;
    link.click();
    URL.revokeObjectURL(url);
  }, []);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;
    
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Add zoom behavior
    const zoomBehavior = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
        setZoom(event.transform.k);
      });

    svg.call(zoomBehavior);

    // Main group for zoom/pan
    const g = svg.append('g');

    // Arrow markers for directed edges
    const defs = svg.append('defs');
    
    ['exploit', 'connection', 'depends', 'leads_to'].forEach((type) => {
      const color = type === 'exploit' ? '#ef4444' : '#6b7280';
      defs
        .append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color);
    });

    // Create simulation
    const simulation = d3
      .forceSimulation<D3Node>(nodes)
      .force(
        'link',
        d3
          .forceLink<D3Node, D3Link>(links)
          .id((d) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Create links
    const link = g
      .append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', (d) => (d.type === 'exploit' ? '#ef4444' : '#4b5563'))
      .attr('stroke-width', (d) => (d.type === 'exploit' ? 3 : 1.5))
      .attr('stroke-dasharray', (d) => (d.type === 'depends' ? '5,5' : 'none'))
      .attr('marker-end', (d) => `url(#arrow-${d.type})`)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation();
        onEdgeClick?.(d as AttackEdge);
      });

    // Link labels
    const linkLabel = g
      .append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(links.filter((d) => d.label))
      .enter()
      .append('text')
      .attr('font-size', 10)
      .attr('fill', '#9ca3af')
      .attr('text-anchor', 'middle')
      .text((d) => d.label || '');

    // Create nodes
    const node = g
      .append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .attr('cursor', 'pointer')
      .call(
        d3
          .drag<SVGGElement, D3Node>()
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
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
        onNodeClick?.(d);
      });

    // Node circles
    node
      .append('circle')
      .attr('r', (d) => (d.type === 'host' ? 25 : 20))
      .attr('fill', (d) => `${nodeColors[d.type]}33`) // 20% opacity
      .attr('stroke', (d) => nodeColors[d.type])
      .attr('stroke-width', 2);

    // Node icons
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('font-size', 16)
      .text((d) => nodeIcons[d.type]);

    // Node labels
    node
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', 35)
      .attr('font-size', 11)
      .attr('fill', '#e5e7eb')
      .text((d) => d.label);

    // Highlight selected path
    if (selectedPath && selectedPath.length > 0) {
      const pathNodeIds = new Set(selectedPath);
      
      node.selectAll('circle')
        .attr('stroke-width', (d: D3Node) => pathNodeIds.has(d.id) ? 4 : 2)
        .attr('opacity', (d: D3Node) => pathNodeIds.has(d.id) ? 1 : 0.3);
      
      link.attr('opacity', (d: D3Link) => {
        const sourceId = typeof d.source === 'string' ? d.source : d.source.id;
        const targetId = typeof d.target === 'string' ? d.target : d.target.id;
        return pathNodeIds.has(sourceId) && pathNodeIds.has(targetId) ? 1 : 0.2;
      });
    }

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as D3Node).x || 0)
        .attr('y1', (d) => (d.source as D3Node).y || 0)
        .attr('x2', (d) => (d.target as D3Node).x || 0)
        .attr('y2', (d) => (d.target as D3Node).y || 0);

      linkLabel
        .attr('x', (d) => (((d.source as D3Node).x || 0) + ((d.target as D3Node).x || 0)) / 2)
        .attr('y', (d) => (((d.source as D3Node).y || 0) + ((d.target as D3Node).y || 0)) / 2);

      node.attr('transform', (d) => `translate(${d.x || 0},${d.y || 0})`);
    });

    return () => {
      simulation.stop();
    };
  }, [data, nodes, links, width, height, onNodeClick, onEdgeClick, selectedPath]);

  return (
    <div ref={containerRef} className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-white">Attack-Graph</h3>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span>{nodes.length} Nodes</span>
            <span>•</span>
            <span>{links.length} Edges</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={exportPNG}
            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            PNG
          </button>
          <button
            onClick={exportSVG}
            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
            </svg>
            SVG
          </button>
          <button
            onClick={toggleFullscreen}
            className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white text-sm rounded-lg transition-colors"
          >
            {isFullscreen ? 'Vollbild beenden' : 'Vollbild'}
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div className="relative">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          className="bg-gray-900"
        />
        
        {/* Zoom indicator */}
        <div className="absolute bottom-4 left-4 bg-gray-800/90 px-3 py-1 rounded-lg text-sm text-gray-400">
          Zoom: {(zoom * 100).toFixed(0)}%
        </div>

        {/* Legend */}
        <div className="absolute top-4 right-4 bg-gray-800/90 p-3 rounded-lg border border-gray-700">
          <h4 className="text-xs font-medium text-gray-400 mb-2">Legende</h4>
          <div className="space-y-1">
            {(Object.entries(nodeIcons) as [NodeType, string][]).map(([type, icon]) => (
              <div key={type} className="flex items-center gap-2">
                <span>{icon}</span>
                <span className="text-xs text-gray-300 capitalize">{type}</span>
              </div>
            ))}
          </div>
          <div className="mt-2 pt-2 border-t border-gray-700 space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-red-500" />
              <span className="text-xs text-gray-300">Exploit</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-gray-500" />
              <span className="text-xs text-gray-300">Connection</span>
            </div>
          </div>
        </div>
      </div>

      {/* Node Details Panel */}
      {selectedNode && (
        <div className="border-t border-gray-700 p-4 bg-gray-800/50">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-2xl">{nodeIcons[selectedNode.type]}</span>
                <h4 className="text-lg font-semibold text-white">{selectedNode.label}</h4>
                <span
                  className="px-2 py-0.5 rounded text-xs font-medium capitalize"
                  style={{
                    backgroundColor: `${nodeColors[selectedNode.type]}33`,
                    color: nodeColors[selectedNode.type],
                  }}
                >
                  {selectedNode.type}
                </span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {selectedNode.data.ip && (
                  <div>
                    <span className="text-gray-500">IP:</span>
                    <span className="text-white ml-2">{selectedNode.data.ip}</span>
                  </div>
                )}
                {selectedNode.data.hostname && (
                  <div>
                    <span className="text-gray-500">Hostname:</span>
                    <span className="text-white ml-2">{selectedNode.data.hostname}</span>
                  </div>
                )}
                {selectedNode.data.port && (
                  <div>
                    <span className="text-gray-500">Port:</span>
                    <span className="text-white ml-2">{selectedNode.data.port}</span>
                  </div>
                )}
                {selectedNode.data.service && (
                  <div>
                    <span className="text-gray-500">Service:</span>
                    <span className="text-white ml-2">{selectedNode.data.service}</span>
                  </div>
                )}
                {selectedNode.data.version && (
                  <div>
                    <span className="text-gray-500">Version:</span>
                    <span className="text-white ml-2">{selectedNode.data.version}</span>
                  </div>
                )}
                {selectedNode.data.cve && (
                  <div>
                    <span className="text-gray-500">CVE:</span>
                    <span className="text-red-400 ml-2">{selectedNode.data.cve}</span>
                  </div>
                )}
                {selectedNode.data.cvss && (
                  <div>
                    <span className="text-gray-500">CVSS:</span>
                    <span
                      className={`ml-2 font-medium ${
                        selectedNode.data.cvss >= 7 ? 'text-red-400' : 'text-yellow-400'
                      }`}
                    >
                      {selectedNode.data.cvss}
                    </span>
                  </div>
                )}
              </div>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AttackGraph;
