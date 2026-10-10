from flask import Flask, jsonify, render_template_string
from statistics import median
from datetime import datetime
from threading import Lock

app = Flask(__name__)
lock = Lock()

# Five simulated servers
nodes = {
    1: {"rate": 100, "online": True},
    2: {"rate": 100, "online": True},
    3: {"rate": 120, "online": True},
    4: {"rate": 100, "online": True},
    5: {"rate": 110, "online": True},
}

links = {
    (1, 2): True, (1, 3): True, (1, 5): True,
    (2, 3): True, (2, 4): True,
    (3, 4): True, (3, 5): True, (4, 5): True
}

events = []


def log_event(message):
    events.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": message
    })
    del events[30:]


def network_connected(active_ids):
    if len(active_ids) <= 1:
        return True

    active = set(active_ids)
    visited = {next(iter(active))}
    stack = list(visited)

    while stack:
        current = stack.pop()

        for (a, b), enabled in links.items():
            if not enabled or a not in active or b not in active:
                continue

            neighbor = b if current == a else (
                a if current == b else None
            )

            if neighbor is not None and neighbor not in visited:
                visited.add(neighbor)
                stack.append(neighbor)

    return visited == active


def get_state():
    active = [
        {"id": i, **node}
        for i, node in nodes.items()
        if node["online"]
    ]

    connected = network_connected([n["id"] for n in active])

    rate = (
        median([n["rate"] for n in active])
        if active and connected else None
    )

    return {
        "nodes": [
            {"id": i, **node}
            for i, node in nodes.items()
        ],
        "links": [
            {"a": a, "b": b, "enabled": enabled}
            for (a, b), enabled in links.items()
        ],
        "active": len(active),
        "rate": rate,
        "connected": connected,
        "status": (
            "No active nodes" if not active else
            "Consensus Active" if connected else
            "Network Partition"
        ),
        "events": events
    }


@app.get("/")
def home():
    return render_template_string(HTML)


@app.get("/api/state")
def api_state():
    with lock:
        return jsonify(get_state())


@app.post("/api/node/<int:node_id>/kill")
def kill_node(node_id):
    with lock:
        if node_id not in nodes:
            return jsonify({"error": "Unknown node"}), 404

        nodes[node_id]["online"] = False
        log_event(f"Node {node_id} failed")
        return jsonify(get_state())


@app.post("/api/node/<int:node_id>/restore")
def restore_node(node_id):
    with lock:
        if node_id not in nodes:
            return jsonify({"error": "Unknown node"}), 404

        nodes[node_id]["online"] = True
        log_event(f"Node {node_id} restored")
        return jsonify(get_state())


@app.post("/api/link/<int:a>/<int:b>/toggle")
def toggle_link(a, b):
    pair = tuple(sorted((a, b)))

    with lock:
        if pair not in links:
            return jsonify({"error": "Unknown link"}), 404

        links[pair] = not links[pair]
        log_event(f"Link {a}-{b} toggled")
        return jsonify(get_state())


@app.post("/api/restore-all")
def restore_all():
    with lock:
        for node in nodes.values():
            node["online"] = True

        for pair in links:
            links[pair] = True

        log_event("All nodes and links restored")
        return jsonify(get_state())


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PS-13 Consensus Dashboard</title>
<style>
body {
    margin: 0;
    padding: 25px;
    font-family: Arial, sans-serif;
    background: #07111f;
    color: #edf5ff;
}
h1 { color: #52d8ef; }
.cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 15px;
}
.card, section {
    background: #12243a;
    border: 1px solid #29415e;
    border-radius: 12px;
    padding: 18px;
    margin-bottom: 15px;
}
.metric { font-size: 26px; font-weight: bold; }
button, select {
    padding: 10px;
    margin: 4px;
    border: 0;
    border-radius: 6px;
}
button { cursor: pointer; background: #2864c5; color: white; }
.kill { background: #bd354d; }
.restore { background: #168563; }
.node {
    display: inline-block;
    padding: 12px;
    margin: 8px;
    border-radius: 10px;
    background: #164b40;
}
.offline { background: #722e3c; }
small { color: #a9bed7; }
</style>
</head>
<body>
<h1>PS-13 | Distributed Rate Consensus</h1>
<p>Interactive Chaos Monkey Topology Visualizer</p>

<div class="cards">
  <div class="card">
    <small>Total Nodes</small>
    <div class="metric">5</div>
  </div>
  <div class="card">
    <small>Active Nodes</small>
    <div class="metric" id="active">5</div>
  </div>
  <div class="card">
    <small>Consensus Rate</small>
    <div class="metric" id="rate">100 req/s</div>
  </div>
  <div class="card">
    <small>System Status</small>
    <div class="metric" id="status">Active</div>
  </div>
</div>

<section>
<h2>Network Topology</h2>
<div id="topology"></div>
</section>

<section>
<h2>Chaos Monkey Controls</h2>
<label for="node">Choose node:</label>
<select id="node">
  <option value="1">Node 1</option>
  <option value="2">Node 2</option>
  <option value="3">Node 3</option>
  <option value="4">Node 4</option>
  <option value="5">Node 5</option>
</select>
<button class="kill" onclick="nodeAction('kill')">Kill Node</button>
<button class="restore" onclick="nodeAction('restore')">Restore Node</button>
<button onclick="restoreAll()">Restore All</button>
</section>

<section>
<h2>Network Link Control</h2>
<select id="link">
  <option value="1-2">Node 1 - Node 2</option>
  <option value="1-3">Node 1 - Node 3</option>
  <option value="1-5">Node 1 - Node 5</option>
  <option value="2-3">Node 2 - Node 3</option>
  <option value="2-4">Node 2 - Node 4</option>
  <option value="3-4">Node 3 - Node 4</option>
  <option value="3-5">Node 3 - Node 5</option>
  <option value="4-5">Node 4 - Node 5</option>
</select>
<button onclick="toggleLink()">Toggle Link</button>
</section>

<section>
<h2>Event Log</h2>
<div id="events">No events yet.</div>
</section>

<script>
async function update() {
    const response = await fetch('/api/state');
    const data = await response.json();

    document.getElementById('active').textContent = data.active;
    document.getElementById('rate').textContent =
        data.rate === null ? 'Unavailable' : data.rate + ' req/s';
    document.getElementById('status').textContent = data.status;

    document.getElementById('topology').innerHTML =
        data.nodes.map(n => `
          <div class="node ${n.online ? '' : 'offline'}">
            <b>Node ${n.id}</b><br>
            ${n.online ? 'Online' : 'Offline'}<br>
            ${n.rate} req/s
          </div>
        `).join('');

    document.getElementById('events').innerHTML =
        data.events.map(e =>
            `<p><small>${e.time}</small> — ${e.message}</p>`
        ).join('') || 'No events yet.';
}

async function nodeAction(action) {
    const id = document.getElementById('node').value;
    await fetch(`/api/node/${id}/${action}`, {method: 'POST'});
    update();
}

async function toggleLink() {
    const [a, b] = document.getElementById('link').value.split('-');
    await fetch(`/api/link/${a}/${b}/toggle`, {method: 'POST'});
    update();
}

async function restoreAll() {
    await fetch('/api/restore-all', {method: 'POST'});
    update();
}

update();
setInterval(update, 5000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    log_event("PS-13 simulation started")
    app.run(host="127.0.0.1", port=5000, debug=False)