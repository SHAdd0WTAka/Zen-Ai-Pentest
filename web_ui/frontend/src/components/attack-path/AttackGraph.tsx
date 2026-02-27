import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Play, RotateCcw, Target } from 'lucide-react';

// Register dagre layout
cytoscape.use(dagre);

interface Node {
  id: string;
  name: string;
  type: string;
  criticality: string;
  compromised: boolean;
}

interface Edge {
  source: string;
  target: string;
  technique_name: string;
  difficulty: string;
}

interface AttackGraphProps {
  nodes: Node[];
  edges: Edge[];
  onNodeSelect?: (node: Node) => void;
  highlightedPath?: string[];
}

const nodeColors: Record<string, string> = {
  entry_point: '#3498db',
  workstation: '#9b59b6',
  server: '#2ecc71',
  database: '#e74c3c',
  domain_controller: '#f39c12',
  web_application: '#1abc9c',
  api_endpoint: '#16a085',
  cloud_resource: '#2980b9',
  container: '#27ae60',
  crown_jewel: '#c0392b',
};



export function AttackGraph({ nodes, edges, onNodeSelect, highlightedPath }: AttackGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...nodes.map((node) => ({
          data: {
            id: node.id,
            label: node.name,
            type: node.type,
            criticality: node.criticality,
            compromised: node.compromised,
            color: nodeColors[node.type] || '#95a5a6',
          },
        })),
        ...edges.map((edge, idx) => ({
          data: {
            id: `edge-${idx}`,
            source: edge.source,
            target: edge.target,
            label: edge.technique_name,
            difficulty: edge.difficulty,
          },
        })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'width': 60,
            'height': 60,
            'border-width': 3,
            'border-color': '#fff',
            'border-opacity': 0.8,
            'font-size': '12px',
            'font-weight': 'bold',
            'text-valign': 'bottom',
            'text-margin-y': 8,
            'color': '#fff',
            'text-background-color': '#000',
            'text-background-opacity': 0.7,
            'text-background-padding': '3px',
            'text-background-shape': 'roundrectangle',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 3,
            'line-color': '#34495e',
            'target-arrow-color': '#34495e',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'color': '#95a5a6',
            'text-background-color': '#1a1a2e',
            'text-background-opacity': 1,
            'text-background-padding': '2px',
          },
        },
        {
          selector: '.highlighted',
          style: {
            'line-color': '#e74c3c',
            'target-arrow-color': '#e74c3c',
            'width': 5,
            'line-style': 'solid',
          },
        },
        {
          selector: '.compromised',
          style: {
            'border-color': '#e74c3c',
            'border-width': 5,
          },
        },
        {
          selector: '.current-step',
          style: {
            'background-color': '#f39c12',
            'width': 80,
            'height': 80,
          },
        },
      ],
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 80,
        rankSep: 100,
        padding: 20,
      } as any,
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeData = nodes.find((n) => n.id === node.id());
      if (nodeData && onNodeSelect) {
        onNodeSelect(nodeData);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [nodes, edges]);

  useEffect(() => {
    if (highlightedPath && cyRef.current) {
      const cy = cyRef.current;

      // Reset previous highlighting
      cy.edges().removeClass('highlighted');
      cy.nodes().removeClass('current-step');

      // Highlight path edges
      for (let i = 0; i < highlightedPath.length - 1; i++) {
        const source = highlightedPath[i];
        const target = highlightedPath[i + 1];

        cy.edges().forEach((edge) => {
          if (edge.data('source') === source && edge.data('target') === target) {
            edge.addClass('highlighted');
          }
        });
      }
    }
  }, [highlightedPath]);

  const simulateAttack = () => {
    if (!highlightedPath || highlightedPath.length === 0) return;

    setIsSimulating(true);
    setCurrentStep(0);

    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= highlightedPath.length - 1) {
          clearInterval(interval);
          setIsSimulating(false);
          return prev;
        }

        // Update graph visualization
        if (cyRef.current) {
          cyRef.current.nodes().removeClass('current-step');
          cyRef.current.getElementById(highlightedPath[prev + 1]).addClass('current-step');
        }

        return prev + 1;
      });
    }, 1500);
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    setCurrentStep(0);
    if (cyRef.current) {
      cyRef.current.nodes().removeClass('current-step');
    }
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center gap-2">
        <Button
          onClick={simulateAttack}
          disabled={isSimulating || !highlightedPath}
          className="bg-red-500 hover:bg-red-600 text-white gap-2"
        >
          <Play className="w-4 h-4" />
          Simulate Attack
        </Button>

        <Button
          onClick={resetSimulation}
          disabled={isSimulating}
          variant="outline"
          className="gap-2"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </Button>

        {isSimulating && (
          <div className="flex items-center gap-2 text-sm text-yellow-500">
            <Target className="w-4 h-4 animate-pulse" />
            Step {currentStep + 1} of {highlightedPath?.length}
          </div>
        )}
      </div>

      {/* Graph Container */}
      <Card className="border-slate-800 bg-slate-900/50 overflow-hidden">
        <div
          ref={containerRef}
          style={{ width: '100%', height: '600px' }}
          className="relative"
        />
      </Card>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs">
        {Object.entries(nodeColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-slate-400 capitalize">{type.replace('_', ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
