import { useState, useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { Target, Play, RotateCcw, Route, AlertTriangle, Shield } from 'lucide-react';
import { mockApi } from '../../lib/mockData';

// Register dagre layout
cytoscape.use(dagre);

const nodeColors: Record<string, string> = {
  entry_point: '#3498db',
  server: '#2ecc71',
  database: '#e74c3c',
  domain_controller: '#f39c12',
  web_application: '#1abc9c',
  crown_jewel: '#c0392b',
};

export function AttackPathPanel() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [graphData, setGraphData] = useState<any>(null);
  const [paths, setPaths] = useState<any[]>([]);
  const [selectedPath, setSelectedPath] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [simulationSteps, setSimulationSteps] = useState<any[]>([]);

  useEffect(() => {
    const loadData = async () => {
      const [graph, pathData] = await Promise.all([
        mockApi.getAttackGraph(),
        mockApi.getAttackPaths(),
      ]);
      setGraphData(graph);
      setPaths(pathData);
      setSelectedPath(pathData[0]);
    };
    loadData();
  }, []);

  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: [
        ...graphData.nodes.map((node: any) => ({
          data: {
            id: node.id,
            label: node.name,
            type: node.type,
            color: nodeColors[node.type] || '#95a5a6',
          },
        })),
        ...graphData.edges.map((edge: any, idx: number) => ({
          data: {
            id: `edge-${idx}`,
            source: edge.source,
            target: edge.target,
            label: edge.technique_name,
          },
        })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'width': 70,
            'height': 70,
            'border-width': 3,
            'border-color': '#fff',
            'font-size': '12px',
            'font-weight': 'bold',
            'text-valign': 'bottom',
            'text-margin-y': 8,
            'color': '#fff',
            'text-background-color': '#000',
            'text-background-opacity': 0.7,
            'text-background-padding': '4px',
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
            'text-background-color': '#0f172a',
            'text-background-opacity': 1,
            'text-background-padding': '3px',
          },
        },
        {
          selector: '.highlighted',
          style: {
            'line-color': '#e74c3c',
            'target-arrow-color': '#e74c3c',
            'width': 5,
          },
        },
        {
          selector: '.current-step',
          style: {
            'background-color': '#f39c12',
            'border-color': '#f39c12',
            'width': 85,
            'height': 85,
          },
        },
      ],
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 100,
        rankSep: 150,
        padding: 30,
      } as any,
    });

    cyRef.current = cy;

    return () => cy.destroy();
  }, [graphData]);

  useEffect(() => {
    if (selectedPath && cyRef.current) {
      const cy = cyRef.current;
      cy.edges().removeClass('highlighted');
      cy.nodes().removeClass('current-step');

      for (let i = 0; i < selectedPath.path.length - 1; i++) {
        const source = selectedPath.path[i];
        const target = selectedPath.path[i + 1];
        cy.edges().forEach((edge) => {
          if (edge.data('source') === source && edge.data('target') === target) {
            edge.addClass('highlighted');
          }
        });
      }
    }
  }, [selectedPath]);

  const simulateAttack = async () => {
    if (!selectedPath) return;
    setIsSimulating(true);
    setCurrentStep(0);

    const result = await mockApi.simulateAttack();
    setSimulationSteps(result.steps);

    // Animate through steps
    for (let i = 0; i < selectedPath.path.length; i++) {
      setCurrentStep(i);
      if (cyRef.current) {
        cyRef.current.nodes().removeClass('current-step');
        cyRef.current.getElementById(selectedPath.path[i]).addClass('current-step');
      }
      await new Promise((resolve) => setTimeout(resolve, 1500));
    }

    setIsSimulating(false);
  };

  const resetSimulation = () => {
    setIsSimulating(false);
    setCurrentStep(0);
    setSimulationSteps([]);
    if (cyRef.current) {
      cyRef.current.nodes().removeClass('current-step');
    }
  };

  if (!graphData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">Entry Points</p>
          <p className="text-2xl font-bold text-cyan-400">
            {graphData.nodes.filter((n: any) => n.type === 'entry_point').length}
          </p>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">Crown Jewels</p>
          <p className="text-2xl font-bold text-red-500">
            {graphData.nodes.filter((n: any) => n.type === 'crown_jewel' || n.criticality === 'critical').length}
          </p>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">Attack Paths</p>
          <p className="text-2xl font-bold text-slate-200">{paths.length}</p>
        </div>
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/50">
          <p className="text-sm text-slate-500">Risk Level</p>
          <p className="text-lg font-bold text-red-500">CRITICAL</p>
        </div>
      </div>

      {/* Attack Graph */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Target className="w-5 h-5 text-red-500" />
            Attack Graph Visualization
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={simulateAttack}
              disabled={isSimulating}
              className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 disabled:bg-slate-800 text-white rounded-lg font-medium transition-colors"
            >
              <Play className="w-4 h-4" />
              {isSimulating ? 'Simulating...' : 'Simulate Attack'}
            </button>
            <button
              onClick={resetSimulation}
              disabled={isSimulating}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 overflow-hidden">
          <div ref={containerRef} style={{ width: '100%', height: '500px' }} />
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 text-xs">
          {Object.entries(nodeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-slate-400 capitalize">{type.replace('_', ' ')}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Attack Paths */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Route className="w-5 h-5 text-cyan-500" />
          Critical Attack Paths
        </h3>

        <div className="grid gap-4">
          {paths.map((path, idx) => (
            <div
              key={idx}
              onClick={() => setSelectedPath(path)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                selectedPath === path
                  ? 'border-cyan-500 bg-cyan-500/10'
                  : 'border-slate-800 bg-slate-900/50 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500/20 text-red-500 font-bold">
                    {idx + 1}
                  </div>
                  <div>
                    <h4 className="font-medium text-slate-200">
                      {path.nodes[0].name} → {path.nodes[path.nodes.length - 1].name}
                    </h4>
                    <p className="text-sm text-slate-500">
                      {path.length} hops • Difficulty: {path.difficulty_score.toFixed(1)}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold ${
                    path.difficulty_score <= 2
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-yellow-500/20 text-yellow-400'
                  }`}
                >
                  {path.difficulty_score <= 2 ? 'EASY' : 'MEDIUM'}
                </span>
              </div>

              {/* Path visualization */}
              <div className="flex items-center gap-2 mt-4">
                {path.nodes.map((node: any, nodeIdx: number) => (
                  <div key={node.id} className="flex items-center">
                    <span
                      className={`px-3 py-1 rounded text-xs ${
                        node.criticality === 'critical'
                          ? 'bg-red-500/20 text-red-400'
                          : node.criticality === 'high'
                          ? 'bg-orange-500/20 text-orange-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      {node.name}
                    </span>
                    {nodeIdx < path.nodes.length - 1 && (
                      <span className="text-slate-600 mx-2">→</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Simulation Results */}
      {simulationSteps.length > 0 && (
        <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/50">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            Attack Simulation Results
          </h3>
          <div className="space-y-3">
            {simulationSteps.map((step, idx) => (
              <div
                key={idx}
                className={`flex items-center gap-4 p-3 rounded-lg ${
                  idx <= currentStep ? 'bg-red-500/10 border border-red-500/20' : 'bg-slate-800/50'
                }`}
              >
                <span className="w-8 h-8 flex items-center justify-center rounded-full bg-slate-800 text-slate-400 font-bold">
                  {step.step}
                </span>
                <div className="flex-1">
                  <p className="font-medium text-slate-200">{step.action}</p>
                  <p className="text-sm text-slate-500">MITRE ATT&CK: {step.technique}</p>
                </div>
                {idx <= currentStep && (
                  <Shield className="w-5 h-5 text-red-500" />
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
