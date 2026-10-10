<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Distributed Raft Consensus & Chaos Monkey Visualizer</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --border-color: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --leader-color: #10b981;
            --candidate-color: #f59e0b;
            --follower-color: #3b82f6;
            --dead-color: #ef4444;
            --accent: #6366f1;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-primary); min-height: 100vh; display: flex; flex-direction: column; }
        header { background: var(--card-bg); border-bottom: 1px solid var(--border-color); padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
        header h1 { font-size: 1.25rem; font-weight: 600; display: flex; align-items: center; gap: 0.5rem; }
        .badge { background: rgba(99, 102, 241, 0.2); color: #818cf8; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; }
        
        main { display: grid; grid-template-columns: 350px 1fr; flex: 1; height: calc(100vh - 65px); overflow: hidden; }
        aside { background: var(--card-bg); border-right: 1px solid var(--border-color); padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; overflow-y: auto; }
        section h2 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem; }
        
        .control-group { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; }
        label { font-size: 0.875rem; color: var(--text-secondary); }
        input, select, button { background: #0f172a; border: 1px solid var(--border-color); color: var(--text-primary); padding: 0.5rem 0.75rem; border-radius: 0.375rem; font-size: 0.875rem; }
        button { background: var(--accent); border: none; font-weight: 500; cursor: pointer; transition: opacity 0.2s; }
        button:hover { opacity: 0.9; }
        button.danger { background: #ef4444; }
        button.secondary { background: #334155; }
        
        .workspace { display: flex; flex-direction: column; position: relative; overflow: hidden; }
        #canvas-container { flex: 1; position: relative; }
        canvas { width: 100%; height: 100%; display: block; }

        .cluster-stats { position: absolute; top: 1rem; right: 1rem; background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(8px); border: 1px solid var(--border-color); padding: 1rem; border-radius: 0.5rem; display: flex; gap: 1.5rem; font-size: 0.875rem; }
        .stat-item { display: flex; flex-direction: column; }
        .stat-value { font-size: 1.25rem; font-weight: 600; color: #818cf8; }

        .logs-panel { height: 180px; background: var(--card-bg); border-top: 1px solid var(--border-color); padding: 1rem; overflow-y: auto; font-family: monospace; font-size: 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
        .log-entry { color: var(--text-secondary); }
        .log-entry.info { color: #38bdf8; }
        .log-entry.success { color: #34d399; }
        .log-entry.warn { color: #fbbf24; }
        .log-entry.error { color: #f87171; }

        .legend { display: flex; gap: 1rem; font-size: 0.75rem; margin-top: auto; }
        .legend-item { display: flex; align-items: center; gap: 0.375rem; }
        .dot { width: 8px; height: 8px; border-radius: 50%; }
    </style>
</head>
<body>

    <header>
        <h1>⚡ Raft Engine & Chaos Monkey <span class="badge">Live Simulator</span></h1>
        <div id="global-term">Term: 1</div>
    </header>

    <main>
        <aside>
            <section>
                <h2>Chaos Controls</h2>
                <div class="control-group">
                    <label>Target Node</label>
                    <select id="target-node">
                        <option value="0">Node 0</option>
                        <option value="1">Node 1</option>
                        <option value="2">Node 2</option>
                        <option value="3">Node 3</option>
                        <option value="4">Node 4</option>
                    </select>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                    <button class="danger" onclick="chaosToggleKill()">Kill / Revive</button>
                    <button class="secondary" onclick="chaosPartition()">Partition</button>
                </div>
            </section>

            <section>
                <h2>Client Propose</h2>
                <div class="control-group">
                    <label>Command Payload</label>
                    <input type="text" id="client-command" value="SET x = 42">
                </div>
                <button onclick="submitClientCommand()">Send to Cluster</button>
            </section>

            <section>
                <h2>Cluster Simulation</h2>
                <div style="display: flex; gap: 0.5rem;">
                    <button class="secondary" onclick="resetCluster()" style="flex: 1;">Reset Cluster</button>
                </div>
            </section>

            <div class="legend">
                <div class="legend-item"><div class="dot" style="background:var(--leader-color)"></div>Leader</div>
                <div class="legend-item"><div class="dot" style="background:var(--candidate-color)"></div>Candidate</div>
                <div class="legend-item"><div class="dot" style="background:var(--follower-color)"></div>Follower</div>
                <div class="legend-item"><div class="dot" style="background:var(--dead-color)"></div>Dead</div>
            </div>
        </aside>

        <div class="workspace">
            <div id="canvas-container">
                <div class="cluster-stats">
                    <div class="stat-item">
                        <span class="stat-label">Active Leader</span>
                        <span class="stat-value" id="stat-leader">None</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Commit Index</span>
                        <span class="stat-value" id="stat-commit">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Network Partitions</span>
                        <span class="stat-value" id="stat-partition">None</span>
                    </div>
                </div>
                <canvas id="topologyCanvas"></canvas>
            </div>
            <div class="logs-panel" id="log-container">
                <div class="log-entry info">[System] Raft consensus engine initialized with 5 nodes.</div>
            </div>
        </div>
    </main>

    <script>
        const NODE_COUNT = 5;
        let nodes = [];
        let messages = [];
        let partitions = [];
        let globalCommitIndex = 0;
        let animationFrameId;

        class RaftNode {
            constructor(id) {
                this.id = id;
                this.state = 'Follower'; // Follower, Candidate, Leader, Dead
                this.currentTerm = 1;
                this.votedFor = null;
                this.log = []; // {term, command}
                this.commitIndex = 0;
                this.lastApplied = 0;
                this.electionTimeout = this.randomTimeout();
                this.heartbeatTimer = 0;
                
                // Leader volatile state
                this.nextIndex = {};
                this.matchIndex = {};

                // UI position
                this.x = 0;
                this.y = 0;
            }

            randomTimeout() {
                return Math.floor(Math.random() * 2000) + 3000; // 3s - 5s
            }
        }

        function initCluster() {
            nodes = [];
            for (let i = 0; i < NODE_COUNT; i++) {
                nodes.push(new RaftNode(i));
            }
            messages = [];
            partitions = [];
            globalCommitIndex = 0;
            logMessage("Cluster reset to initial state.", "info");
        }

        function logMessage(text, type = '') {
            const container = document.getElementById('log-container');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            const time = new Date().toLocaleTimeString();
            entry.textContent = `[${time}] ${text}`;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }

        // Canvas Setup
        const canvas = document.getElementById('topologyCanvas');
        const ctx = canvas.getContext('2d');

        function resizeCanvas() {
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
        }
        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        function updateNodePositions() {
            const cx = canvas.width / 2;
            const cy = canvas.height / 2;
            const radius = Math.min(cx, cy) - 100;
            
            nodes.forEach((node, i) => {
                const angle = (i / NODE_COUNT) * 2 * Math.PI - Math.PI / 2;
                node.x = cx + radius * Math.cos(angle);
                node.y = cy + radius * Math.sin(angle);
            });
        }

        // Simulation Step
        let lastTime = performance.now();
        function simulate(currentTime) {
            const dt = currentTime - lastTime;
            lastTime = currentTime;

            updateNodePositions();

            // Run state logic for live nodes
            nodes.forEach(node => {
                if (node.state === 'Dead') return;

                if (node.state === 'Leader') {
                    node.heartbeatTimer += dt;
                    if (node.heartbeatTimer > 1000) { // Send heartbeat every 1s
                        node.heartbeatTimer = 0;
                        sendHeartbeats(node);
                    }
                } else {
                    node.electionTimeout -= dt;
                    if (node.electionTimeout <= 0) {
                        startElection(node);
                    }
                }
            });

            render();
            animationFrameId = requestAnimationFrame(simulate);
        }

        function startElection(node) {
            node.state = 'Candidate';
            node.currentTerm++;
            node.votedFor = node.id;
            node.electionTimeout = node.randomTimeout();
            logMessage(`Node ${node.id} timed out. Starting election for Term ${node.currentTerm}.`, "warn");

            let votes = 1;
            nodes.forEach(peer => {
                if (peer.id === node.id || peer.state === 'Dead') return;
                if (isPartitioned(node.id, peer.id)) return;

                // Request vote simulation
                if (peer.currentTerm < node.currentTerm) {
                    peer.currentTerm = node.currentTerm;
                    peer.votedFor = node.id;
                    votes++;
                    logMessage(`Node ${peer.id} voted for Node ${node.id} in Term ${node.currentTerm}.`, "info");
                }
            });

            if (votes > NODE_COUNT / 2) {
                node.state = 'Leader';
                logMessage(`Node ${node.id} elected Leader for Term ${node.currentTerm}!`, "success");
                nodes.forEach(p => {
                    node.nextIndex[p.id] = node.log.length + 1;
                    node.matchIndex[p.id] = 0;
                });
                sendHeartbeats(node);
            }
        }

        function sendHeartbeats(leader) {
            nodes.forEach(peer => {
                if (peer.id === leader.id || peer.state === 'Dead') return;
                if (isPartitioned(leader.id, peer.id)) return;
                
                peer.state = 'Follower';
                peer.electionTimeout = leader.randomTimeout();
                if (peer.currentTerm < leader.currentTerm) {
                    peer.currentTerm = leader.currentTerm;
                }
            });
        }

        function isPartitioned(id1, id2) {
            return partitions.some(p => p.includes(id1) && p.includes(id2) && (!p.includes(id1) || !p.includes(id2))); 
            // Simple split check: if partition list contains isolated groups
        }

        function chaosToggleKill() {
            const id = parseInt(document.getElementById('target-node').value);
            const node = nodes[id];
            if (node.state === 'Dead') {
                node.state = 'Follower';
                node.electionTimeout = node.randomTimeout();
                logMessage(`Chaos Monkey: Revived Node ${id}.`, "success");
            } else {
                node.state = 'Dead';
                logMessage(`Chaos Monkey: Killed Node ${id}!`, "error");
            }
        }

        function chaosPartition() {
            // Isolate target node from others
            const id = parseInt(document.getElementById('target-node').value);
            partitions = [[id], nodes.filter(n => n.id !== id).map(n => n.id)];
            logMessage(`Chaos Monkey: Isolated Node ${id} in network partition!`, "error");
            document.getElementById('stat-partition').textContent = `Node ${id} Isolated`;
        }

        function submitClientCommand() {
            const cmd = document.getElementById('client-command').value;
            const leader = nodes.find(n => n.state === 'Leader');
            if (!leader) {
                logMessage(`Client Request Failed: No active leader found in cluster.`, "error");
                return;
            }
            leader.log.push({ term: leader.currentTerm, command: cmd });
            globalCommitIndex = leader.log.length;
            document.getElementById('stat-commit').textContent = globalCommitIndex;
            logMessage(`Leader (Node ${leader.id}) accepted client entry: "${cmd}"`, "success");
        }

        function resetCluster() {
            initCluster();
            document.getElementById('stat-partition').textContent = 'None';
        }

        // Render Loop
        function render() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw connections
            ctx.strokeStyle = '#334155';
            ctx.lineWidth = 2;
            for (let i = 0; i < nodes.length; i++) {
                for (let j = i + 1; j < nodes.length; j++) {
                    if (isPartitioned(nodes[i].id, nodes[j].id)) continue;
                    ctx.beginPath();
                    ctx.moveTo(nodes[i].x, nodes[i].y);
                    ctx.lineTo(nodes[j].x, nodes[j].y);
                    ctx.stroke();
                }
            }

            // Draw nodes
            nodes.forEach(node => {
                ctx.beginPath();
                ctx.arc(node.x, node.y, 32, 0, 2 * Math.PI);
                
                let color = 'var(--follower-color)';
                if (node.state === 'Leader') color = '#10b981';
                else if (node.state === 'Candidate') color = '#f59e0b';
                else if (node.state === 'Dead') color = '#ef4444';
                
                ctx.fillStyle = color;
                ctx.fill();
                ctx.lineWidth = 3;
                ctx.strokeStyle = '#ffffff';
                ctx.stroke();

                // Node Label
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 14px system-ui';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(`N${node.id}`, node.x, node.y - 6);

                ctx.font = '10px system-ui';
                ctx.fillText(`T:${node.currentTerm}`, node.x, node.y + 10);
            });

            // Update stats header
            const leader = nodes.find(n => n.state === 'Leader');
            document.getElementById('stat-leader').textContent = leader ? `Node ${leader.id}` : 'None';
            const activeTerm = nodes.length > 0 ? nodes[0].currentTerm : 1;
            document.getElementById('global-term').textContent = `Term: ${activeTerm}`;
        }

        initCluster();
        requestAnimationFrame(simulate);
    </script>
</body>
</html>