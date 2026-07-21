"""
generate_agentcoordkg_convergence_figure.py

展示AgentCoordKG最强的实证发现:4个架构完全不同的框架,各自的原生
编排概念,全部收敛到同一个dependsOn关系上。

Colab运行方式同HarnessKG那份:
  !apt-get install -y graphviz -q
  !pip install graphviz -q
"""

from graphviz import Digraph

dot = Digraph("Convergence", format="svg")
dot.attr(rankdir="LR", splines="line", nodesep="0.35", ranksep="0.9", bgcolor="white")
dot.attr("node", fontname="Helvetica", fontsize="12", shape="box", style="rounded")
dot.attr("edge", fontname="Helvetica", fontsize="10", color="#4a5a68")

# 左侧:4个框架各自的原生概念(空心方框,浅色描边,标注框架名字)
framework_style = {"color": "#5a6a75", "fontcolor": "#2c3e50"}
dot.node("crewai", "CrewAI\nProcess", **framework_style)
dot.node("autogen", "AutoGen\nGroupChatManager", **framework_style)
dot.node("langgraph", "LangGraph\nEdge", **framework_style)
dot.node("metagpt", "MetaGPT\nSOP", **framework_style)

# 右侧:AgentCoordKG的dependsOn(重点强调,粗描边+主题色)
dot.node("dependsOn", "AgentCoordKG\ndependsOn", color="#2a9d94", fontcolor="#0d1117",
         penwidth="2.5", style="rounded,filled", fillcolor="#e8f7f5")

# 收敛箭头
for src in ["crewai", "autogen", "langgraph", "metagpt"]:
    dot.edge(src, "dependsOn")

dot.render("agentcoordkg_convergence", cleanup=True)
print("已生成 agentcoordkg_convergence.svg")
