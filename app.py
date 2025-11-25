import streamlit as st
import random
import math
import networkx as nx
from pyvis.network import Network
import tempfile
import os

# -------------------------------------------------------
# BASIC CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="Real-Time WMN Simulator", layout="wide")
st.title("🛰️ Real-Time Wireless Mesh Network Simulator (RT-WMNSIM)")
st.caption("A Real-Time, Dataset-Free, Model-Free WMN Simulation System")

# -------------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------------
st.sidebar.header("Simulation Parameters")

num_nodes = st.sidebar.slider("Total Nodes", 5, 50, 20)
tx_range = st.sidebar.slider("Transmission Range", 50, 300, 150)
selfish_ratio = st.sidebar.slider("Selfish Nodes (%)", 0, 80, 20)
mobility = st.sidebar.checkbox("Enable Mobility", True)
multi_radio = st.sidebar.checkbox("Multi-Radio Routing", True)
multi_channel = st.sidebar.checkbox("Multi-Channel MAC", True)

# -------------------------------------------------------
# NODE GENERATION
# -------------------------------------------------------
nodes = {}
G = nx.Graph()

for i in range(num_nodes):
    nodes[i] = {
        "x": random.randint(0, 800),
        "y": random.randint(0, 500),
        "power": random.randint(70, 100),
        "trust": 100,
        "selfish": False
    }

# Assign selfish nodes
selfish_nodes = random.sample(list(nodes.keys()), int(num_nodes * selfish_ratio / 100))
for sn in selfish_nodes:
    nodes[sn]["selfish"] = True
    nodes[sn]["trust"] = random.randint(20, 60)

# -------------------------------------------------------
# BUILD WMN LINKS
# -------------------------------------------------------
for i in nodes:
    for j in nodes:
        if i != j:
            dist = math.dist((nodes[i]["x"], nodes[i]["y"]), (nodes[j]["x"], nodes[j]["y"]))
            if dist <= tx_range:
                capacity = max(1, 100 - int(dist / 3))
                if multi_radio:
                    capacity += 20
                if multi_channel:
                    capacity += 15
                G.add_edge(i, j, weight=dist, capacity=capacity)

# -------------------------------------------------------
# ROUTING FUNCTION
# -------------------------------------------------------
def find_route(src, dst):
    try:
        path = nx.shortest_path(G, src, dst, weight="weight")
        return path
    except:
        return None

# -------------------------------------------------------
# PACKET DELIVERY SIMULATION
# -------------------------------------------------------
def send_packet(src, dst):
    path = find_route(src, dst)
    if not path:
        return None, "No Path Found"

    delivered = True
    for hop in path:
        if nodes[hop]["selfish"]:
            if random.random() < 0.6:
                nodes[hop]["trust"] -= 5
                return path, "Dropped by selfish node"
        nodes[hop]["power"] -= random.randint(1, 5)

    return path, "Delivered"

# -------------------------------------------------------
# RUN SIMULATION
# -------------------------------------------------------
src = random.randint(0, num_nodes - 1)
dst = random.randint(0, num_nodes - 1)
path, status = send_packet(src, dst)

# -------------------------------------------------------
# VISUALIZATION (FIXED)
# -------------------------------------------------------
net = Network(height="600px", width="100%", bgcolor="#222", font_color="white")
net.barnes_hut()

# Add nodes
for i in nodes:
    color = "orange" if nodes[i]["selfish"] else "lightblue"
    title = f"Node {i}<br>Power: {nodes[i]['power']}%<br>Trust: {nodes[i]['trust']}"
    net.add_node(i, label=str(i), x=nodes[i]["x"], y=nodes[i]["y"], color=color, title=title)

# Add edges
for u, v in G.edges():
    cap = G[u][v]["capacity"]
    net.add_edge(u, v, label=str(cap))

# Create correct temporary HTML file
tmp_html = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
net.write_html(tmp_html.name)

# -------------------------------------------------------
# DISPLAY RESULTS
# -------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("WMN Topology")
    st.components.v1.html(open(tmp_html.name, "r").read(), height=600)

with col2:
    st.subheader("Simulation Result")
    st.write(f"**Source:** {src}")
    st.write(f"**Destination:** {dst}")
    st.write(f"**Route:** {path}")
    st.write(f"**Status:** {status}")

    selfish_list = [n for n in nodes if nodes[n]["selfish"]]
    st.write("### Selfish Nodes:", selfish_list)

    st.subheader("Network Statistics")
    st.write("Total Links:", len(G.edges()))
    st.write("Average Node Power:", sum([nodes[i]["power"] for i in nodes]) / num_nodes)
    st.write("Average Trust Level:", sum([nodes[i]["trust"] for i in nodes]) / num_nodes)
