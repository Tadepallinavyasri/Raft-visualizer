NODES = {
    f"N{i}": {"online": True}
    for i in range(1, 6)
}

LINKS = {
    ("N1", "N2"),
    ("N1", "N3"),
    ("N2", "N4"),
    ("N3", "N5"),
    ("N4", "N5"),
}


def can_communicate(source, target):
    if source not in NODES or target not in NODES:
        return False

    if not NODES[source]["online"]:
        return False

    if not NODES[target]["online"]:
        return False

    return (
        (source, target) in LINKS
        or (target, source) in LINKS
    )


def send_message(source, target, message):
    if can_communicate(source, target):
        return f"{source} -> {target}: {message}"

    return f"Message failed: {source} and {target} cannot communicate."


def kill_node(node):
    if node in NODES:
        NODES[node]["online"] = False
        return f"{node} is offline."

    return "Unknown node."


def restore_node(node):
    if node in NODES:
        NODES[node]["online"] = True
        return f"{node} is online."

    return "Unknown node."


def get_network_state():
    return {
        "nodes": NODES,
        "links": [
            {"source": a, "target": b}
            for a, b in LINKS
        ],
    }


if __name__ == "__main__":
    print("PS-13 Shared Node Network")
    print("Nodes:", list(NODES))
    print(send_message("N1", "N2", "Hello"))

    print(kill_node("N2"))
    print(send_message("N1", "N2", "Test"))

    print(restore_node("N2"))
    print(send_message("N1", "N2", "Recovered"))