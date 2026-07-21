"""
generate_agentcoordkg_schema_figure.py

AgentCoordKG的Ontology Schema图,7个Class、10条Object Property,
配色用青绿/紫色调,与HarnessKG的蓝橙配色区分开。

Colab运行方式:
  !apt-get install -y graphviz -q
  !pip install graphviz -q
"""

from graphviz import Digraph

dot = Digraph("AgentCoordKG_Schema", format="svg")
dot.attr(rankdir="TB", splines="spline", nodesep="0.45", ranksep="0.55", bgcolor="white")
dot.attr("node", fontname="Helvetica", fontsize="12")
dot.attr("edge", fontname="Helvetica", fontsize="10")

# ---- PROV-O 上层类(共享自HarnessKG的三个对齐关系) ----
prov_style = {"shape": "box", "style": "dashed,rounded", "color": "#7a7a7a", "fontcolor": "#555555"}
dot.node("prov_Agent", "prov:Agent", **prov_style)
dot.node("prov_Activity", "prov:Activity", **prov_style)
dot.node("prov_Entity", "prov:Entity", **prov_style)

# ---- AgentCoordKG的7个Class ----
def ak_style(color, bold=False):
    s = {"shape": "box", "style": "rounded", "color": color}
    if bold:
        s["penwidth"] = "2.2"
    return s

dot.node("Agent", "ak:Agent", **ak_style("#2a9d94", bold=True))
dot.node("Task", "ak:Task", **ak_style("#7a4fc0", bold=True))
dot.node("Message", "ak:Message", **ak_style("#4a9ec8"))
dot.node("Decision", "ak:Decision", **ak_style("#d6a94a"))
dot.node("Conflict", "ak:Conflict", **ak_style("#c85a5a", bold=True))
dot.node("Constraint", "ak:Constraint", **ak_style("#7a8590"))
dot.node("Environment", "ak:Environment", **ak_style("#4ab06a"))

# ---- subClassOf 关系(虚线,共享概念对齐PROV-O) ----
subclass_style = {"style": "dashed", "color": "#7a7a7a", "fontcolor": "#7a7a7a",
                   "arrowhead": "empty", "label": "subClassOf"}
dot.edge("Agent", "prov_Agent", **subclass_style)
dot.edge("Decision", "prov_Activity", **subclass_style)
dot.edge("Environment", "prov_Entity", **subclass_style)

# ---- 10条Object Property ----
prop_style = {"color": "#2c3e50", "fontcolor": "#2a9d94"}
task_style = {"color": "#2c3e50", "fontcolor": "#7a4fc0"}

dot.edge("Agent", "Message", label="sendsMessage", **prop_style)
dot.edge("Agent", "Task", label="delegatesTask", **prop_style)
dot.edge("Agent", "Environment", label="actsWithin", **prop_style)
dot.edge("Task", "Agent", label="assignedTo", **task_style)
dot.edge("Task", "Constraint", label="violatesConstraint", **task_style)
dot.edge("Task", "Conflict", label="resolvesConflict", **task_style)
dot.edge("Task", "Task", label="dependsOn", **task_style)
dot.edge("Task", "Environment", label="occursIn", **task_style)
dot.edge("Message", "Decision", label="supportsDecision", color="#2c3e50", fontcolor="#4a9ec8")
dot.edge("Conflict", "Agent", label="involvesAgent", color="#2c3e50", fontcolor="#c85a5a")

dot.render("agentcoordkg_schema", cleanup=True)
print("已生成 agentcoordkg_schema.svg")
