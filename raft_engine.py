import random
import threading


class RaftNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.state = "Follower"
        self.alive = True
        self.log = []


class RaftEngine:
    def __init__(self, node_count=5):
        self.lock = threading.RLock()
        self.nodes = [
            RaftNode(i + 1) for i in range(node_count)
        ]
        self.leader_id = None
        self.elect_leader()

    def elect_leader(self):
        with self.lock:
            candidates = [
                node for node in self.nodes
                if node.alive
            ]

            self.leader_id = None

            for node in self.nodes:
                node.state = (
                    "Follower" if node.alive else "Failed"
                )

            if candidates:
                leader = random.choice(candidates)
                leader.state = "Leader"
                self.leader_id = leader.node_id

            return self.get_state()

    def fail_node(self, node_id):
        with self.lock:
            node = self._find_node(node_id)
            if node is None:
                return {"error": "Node not found"}

            node.alive = False
            node.state = "Failed"

            if self.leader_id == node_id:
                self.elect_leader()

            return self.get_state()

    def restore_node(self, node_id):
        with self.lock:
            node = self._find_node(node_id)
            if node is None:
                return {"error": "Node not found"}

            node.alive = True
            node.state = "Follower"

            if self.leader_id is None:
                self.elect_leader()

            return self.get_state()

    def add_log_entry(self, command):
        with self.lock:
            if self.leader_id is None:
                return {
                    "success": False,
                    "message": "No active leader"
                }

            leader = self._find_node(self.leader_id)
            leader.log.append(command)

            return {
                "success": True,
                "message": "Log added to leader",
                "leader_id": self.leader_id
            }

    def _find_node(self, node_id):
        return next(
            (n for n in self.nodes if n.node_id == node_id),
            None
        )

    def get_state(self):
        with self.lock:
            return {
                "leader_id": self.leader_id,
                "nodes": [
                    {
                        "id": n.node_id,
                        "state": n.state,
                        "alive": n.alive,
                        "log": list(n.log)
                    }
                    for n in self.nodes
                ]
            }


if __name__ == "__main__":
    engine = RaftEngine(5)
    print("Initial state:", engine.get_state())

    failed_id = engine.leader_id
    print("Failing leader:", failed_id)
    print(engine.fail_node(failed_id))

    print("Restoring node:", failed_id)
    print(engine.restore_node(failed_id))