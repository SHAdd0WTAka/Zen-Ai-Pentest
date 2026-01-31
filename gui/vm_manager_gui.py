"""
Web-basierte GUI für VM Management

Flask + React-basierte Oberfläche für VirtualBox und Cloud-VMs.
"""

import json
import logging
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# HTML Template mit React
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zen-AI-Pentest VM Manager</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header {
            background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }
        h1 { color: #58a6ff; font-size: 28px; margin-bottom: 10px; }
        .subtitle { color: #8b949e; }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #30363d;
            padding-bottom: 10px;
        }
        .tab {
            padding: 10px 20px;
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            cursor: pointer;
            color: #c9d1d9;
            transition: all 0.2s;
        }
        .tab:hover { background: #30363d; }
        .tab.active {
            background: #1f6feb;
            border-color: #58a6ff;
            color: white;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
        }
        
        .vm-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .vm-name {
            font-size: 18px;
            font-weight: 600;
            color: #e6edf3;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-running { background: #238636; color: white; }
        .status-stopped { background: #8957e5; color: white; }
        
        .actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }
        .btn-primary { background: #1f6feb; color: white; }
        .btn-success { background: #238636; color: white; }
        .btn-danger { background: #da3633; color: white; }
        .btn-secondary { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const App = () => {
            const [vms, setVms] = React.useState([
                { id: '1', name: 'kali-pentest', state: 'running', type: 'Kali Linux', provider: 'VirtualBox' },
                { id: '2', name: 'win10-target', state: 'stopped', type: 'Windows 10', provider: 'VirtualBox' },
                { id: '3', name: 'aws-kali-01', state: 'running', type: 'Kali Linux', provider: 'AWS', ip: '54.123.45.67' }
            ]);
            
            return (
                <div className="container">
                    <header>
                        <h1>Zen-AI-Pentest VM Manager</h1>
                        <p className="subtitle">Manage VirtualBox and Cloud VMs</p>
                    </header>
                    
                    <div className="tabs">
                        <button className="tab active">VirtualBox</button>
                        <button className="tab">Cloud VMs</button>
                    </div>
                    
                    <div className="grid">
                        {vms.map(vm => (
                            <div key={vm.id} className="card">
                                <div className="vm-header">
                                    <span className="vm-name">{vm.name}</span>
                                    <span className={`status-badge status-${vm.state}`}>{vm.state}</span>
                                </div>
                                <div style={{marginBottom: '15px', fontSize: '14px', color: '#8b949e'}}>
                                    <div>Provider: {vm.provider}</div>
                                    <div>Type: {vm.type}</div>
                                    {vm.ip && <div>IP: {vm.ip}</div>}
                                </div>
                                <div className="actions">
                                    {vm.state !== 'running' && (
                                        <button className="btn btn-success">Start</button>
                                    )}
                                    {vm.state === 'running' && (
                                        <button className="btn btn-secondary">Stop</button>
                                    )}
                                    <button className="btn btn-primary">Snapshot</button>
                                    <button className="btn btn-danger">Delete</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            );
        };
        
        ReactDOM.createRoot(document.getElementById('root')).render(<App />);
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/vms')
def get_vms():
    return jsonify({"vms": []})


def start_gui(host='0.0.0.0', port=8080, debug=False):
    print(f"Starting GUI at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    start_gui(debug=True)
