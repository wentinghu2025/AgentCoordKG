"""
build_agentcoordkg_demo.py

在Google Colab里生成一个可以直接查看/部署的静态HTML展示页面(AgentCoordKG版本),涵盖:
  - 场景选择器(目前1个illustrative场景,后续可迭代加真实框架场景)
  - KG可视化(点节点看定义+溯源到Citation)
  - CQ按钮(显示预先算好的自然语言答案,英文展示)
  - Evidence-grounded Questions面板(来自Poster2 Stage A语料的真实证据)

视觉风格:深色主题+青绿/紫色调,与HarnessKG的浅色暖色调demo区分开,
避免两份Poster的Demo看起来像同一套东西改了名字。

不需要 Streamlit / ngrok / 任何服务器 —— 纯 HTML + vis-network(CDN加载)。
Colab里用 IPython.display.HTML 直接预览,也可以下载后部署到 GitHub Pages。

按 "# ===== CELL N =====" 分隔,依次粘贴进 Colab 的不同代码单元格运行。
"""

# ===== CELL 1: 安装依赖 =====
# !pip install rdflib -q


# ===== CELL 2: 上传文件 =====
# from google.colab import files
# print("请依次上传以下2个文件:")
# print("1) AgentCoordKG.ttl (本体schema)")
# print("2) agentcoordkg_illustrative_case.json (illustrative场景)")
# uploaded = files.upload()


# ===== CELL 3: 加载本体+场景,生成KG,跑CQ,打包成demo_data =====

import json
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef, OWL
from rdflib.namespace import XSD

PROV = Namespace("http://www.w3.org/ns/prov#")


def infer_ontology_namespace(g):
    """从图里第一个owl:Class的URI自动推断命名空间,不写死任何本体的具体URL。
    这样同一份脚本改一下ONTOLOGY_FILE/SCENARIOS/CQ_DEFINITIONS的内容,
    就能套用到任何本体,不需要在多处手动替换命名空间字符串
    (这是2026-07-18从json_to_rdf.py的硬编码bug里吸取的教训)。"""
    for cls in g.subjects(RDF.type, OWL.Class):
        ns = str(cls)
        if "#" in ns:
            return Namespace(ns.rsplit("#", 1)[0] + "#")
    raise ValueError("无法从本体文件推断命名空间")


ONTOLOGY_FILE = "AgentCoordKG.ttl"
SCENARIOS = [
    {"name": "Task Delegation with Conflict Resolution", "file": "agentcoordkg_illustrative_case.json"},
    {"name": "CrewAI-style Content Production Crew", "file": "agentcoordkg_crewai_case.json"},
    {"name": "AutoGen-style Complaint Escalation Coordination", "file": "agentcoordkg_autogen_case.json"},
    {"name": "LangGraph-style Approval Routing Graph", "file": "agentcoordkg_langgraph_case.json"},
    {"name": "MetaGPT-style SOP-Governed Procurement Approval", "file": "agentcoordkg_metagpt_case.json"},
    {"name": "OpenAI Agents SDK-style Triage Handoff", "file": "agentcoordkg_openai_agents_sdk_case.json"},
    {"name": "Trip Planning Team with Budget Conflict", "file": "agentcoordkg_trip_planning_case.json"},
    {"name": "Workflow Compliance Audit", "file": "agentcoordkg_workflow_audit_case.json"},
]

CQ_DEFINITIONS = [
    {
        "cq_id": "CQ1",
        "question": "Which Agent delegated which Task?",
        "purpose": "Task delegation is the basic coordination primitive in multi-agent systems. Knowing who delegated a task is essential for accountability and for tracing a task's origin back to its initiating agent.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?agent ?task WHERE { ?agent ns:delegatesTask ?task . }
        """,
        "nl_template": "{agent} delegated {task}.",
    },
    {
        "cq_id": "CQ2",
        "question": "Which Task violates which Constraint?",
        "purpose": "Detecting constraint violations early is essential for governance. This question identifies exactly which task triggered a compliance issue and which rule it broke, forming the first half of an audit trail.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?task ?constraint WHERE { ?task ns:violatesConstraint ?constraint . }
        """,
        "nl_template": "{task} violates {constraint}.",
    },
    {
        "cq_id": "CQ3",
        "question": "Which Agents are involved in a given Conflict?",
        "purpose": "Once a conflict is detected, a coordinator needs to know precisely which agents are party to it, since the appropriate resolution strategy (renegotiation, escalation, reassignment) depends on knowing all stakeholders.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?conflict ?agent WHERE { ?conflict ns:involvesAgent ?agent . }
        """,
        "nl_template": "{agent} is involved in {conflict}.",
    },
    {
        "cq_id": "CQ4",
        "question": "Which Task resolves which Conflict?",
        "purpose": "This closes the governance loop opened by CQ2/CQ3: it shows not just that a conflict was detected, but what concrete corrective action addressed it, completing the audit trail.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?task ?conflict WHERE { ?task ns:resolvesConflict ?conflict . }
        """,
        "nl_template": "{task} resolves {conflict}.",
    },
    {
        "cq_id": "CQ5",
        "question": "For a given Conflict, which Agents are involved and which Task resolves it?",
        "purpose": "This combines CQ3 and CQ4 into a single query, grouping closely related questions into one comprehensive view for end-user explanation -- who was affected, and how it was fixed, in one answer.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?conflict ?agent ?resolvingTask WHERE {
                ?conflict ns:involvesAgent ?agent .
                ?resolvingTask ns:resolvesConflict ?conflict .
            }
        """,
        "nl_template": "{agent} is involved in {conflict}, which is resolved by {resolvingTask}.",
    },
    {
        "cq_id": "CQ6",
        "question": "Which Agent sends which Message, and which Decision does that Message support?",
        "purpose": "Traces a message from its sender through to the decision it justifies, connecting communication to governance outcome in a single query -- who said what, and what did it lead to.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?agent ?message ?decision WHERE {
                ?agent ns:sendsMessage ?message .
                ?message ns:supportsDecision ?decision .
            }
        """,
        "nl_template": "{agent} sends {message}, which supports {decision}.",
    },
    {
        "cq_id": "CQ7",
        "question": "Which Agent acts within which Environment, and which Task is assigned to that Agent?",
        "purpose": "Connects an agent's operating context to its workload, useful for auditing whether an agent's assigned tasks are consistent with the environment it is authorized to act within.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?agent ?environment ?task WHERE {
                ?agent ns:actsWithin ?environment .
                ?task ns:assignedTo ?agent .
            }
        """,
        "nl_template": "{agent} acts within {environment} and is assigned {task}.",
    },
    {
        "cq_id": "CQ8",
        "question": "Which Task depends on which other Task?",
        "purpose": "Surfaces task-ordering dependencies directly -- the same dependsOn relation independently confirmed across four of the five frameworks studied (Discussion, Semantic Coordination), now queryable at the instance level.",
        "sparql": """
            PREFIX ns: <__NS__>
            SELECT ?task ?dependency WHERE { ?task ns:dependsOn ?dependency . }
        """,
        "nl_template": "{task} depends on {dependency}.",
    },
]


def short(uri):
    # 注意: NS在模块靠后的位置才被赋值(加载完Schema后推断出来),
    # 但这个函数只在NS已经赋值之后才会被实际调用,所以运行时没有问题。
    for prefix in (str(NS), str(PROV), str(XSD)):
        if str(uri).startswith(prefix):
            return str(uri)[len(prefix):]
    return str(uri)


def build_scenario_graph(ontology_path, json_path):
    g = Graph()
    g.parse(ontology_path, format="turtle")
    local_ns = infer_ontology_namespace(g)
    g.bind("ns", local_ns)
    g.bind("prov", PROV)

    with open(json_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    RESERVED_KEYS = {"id", "type", "label", "derivedFromCitation"}

    citation_ids = set()
    for inst in scenario["instances"]:
        if "derivedFromCitation" in inst:
            citation_ids.add(inst["derivedFromCitation"])
    for cit_id in citation_ids:
        cit_uri = local_ns["Citation_" + cit_id]
        g.add((cit_uri, RDF.type, local_ns.Citation))
        g.add((cit_uri, RDFS.label, Literal(cit_id)))

    for inst in scenario["instances"]:
        inst_uri = local_ns[inst["id"]]
        g.add((inst_uri, RDF.type, local_ns[inst["type"]]))
        if "label" in inst:
            g.add((inst_uri, RDFS.label, Literal(inst["label"])))
        for key, value in inst.items():
            if key in RESERVED_KEYS:
                continue
            g.add((inst_uri, local_ns[key], Literal(value, datatype=XSD.string)))
        if "derivedFromCitation" in inst:
            g.add((inst_uri, PROV.wasDerivedFrom, local_ns["Citation_" + inst["derivedFromCitation"]]))

    for rel in scenario["relations"]:
        g.add((local_ns[rel["subject"]], local_ns[rel["property"]], local_ns[rel["object"]]))

    return g, scenario


def extract_nodes_edges(g, scenario):
    """把RDF图,转换成前端vis-network需要的 nodes/edges 格式,
    并且给每个节点带上本体定义(rdfs:comment)和溯源信息。"""
    nodes = {}
    edges = []
    local_ns = infer_ontology_namespace(g)

    for inst in scenario["instances"]:
        inst_uri = local_ns[inst["id"]]
        cls_uri = local_ns[inst["type"]]
        comment = g.value(cls_uri, RDFS.comment)
        citation = None
        for _, _, cit in g.triples((inst_uri, PROV.wasDerivedFrom, None)):
            citation = short(cit)

        nodes[inst["id"]] = {
            "id": inst["id"],
            "label": inst.get("label", inst["id"]),
            "group": inst["type"],
            "definition": str(comment) if comment else "(no definition found)",
            "citation": citation,
        }

    for rel in scenario["relations"]:
        edges.append({
            "from": rel["subject"],
            "to": rel["object"],
            "label": rel["property"],
        })

    return list(nodes.values()), edges


def run_cqs(g):
    results = []
    for cq in CQ_DEFINITIONS:
        sparql_text = cq["sparql"].replace("__NS__", str(NS))
        result = g.query(sparql_text)
        var_names = [str(v) for v in result.vars]
        rows = list(result)
        answers = []
        for row in rows:
            bindings = {var_names[i]: short(row[i]) for i in range(len(var_names))}
            answers.append(cq["nl_template"].format(**bindings))
        results.append({
            "cq_id": cq["cq_id"],
            "question": cq["question"],
            "purpose": cq["purpose"],
            "sparql": sparql_text.strip(),
            "nl_template_raw": cq["nl_template"],
            "answers": answers if answers else ["(no result found in this scenario)"],
        })
    return results


demo_data = {"scenarios": [], "ontology_browser": []}

# ---- Layer 2: Ontology Browser(独立于任何场景,浏览本体schema本身) ----
_g_schema = Graph()
_g_schema.parse(ONTOLOGY_FILE, format="turtle")

# 命名空间自动从本体文件推断,不写死具体本体的URL(全局只需要推断一次)
NS = infer_ontology_namespace(_g_schema)

import pandas as pd
_evidence_df = pd.read_csv("canonical_alignment_table.csv")
_evidence_lookup = {}
for _, _row in _evidence_df.iterrows():
    _concept = _row["Normalized Concept"]
    # 同一个概念可能有多行(比如Environment有跨Poster的更新版本),后出现的行会覆盖前面的,取信息最完整的一条
    _evidence_lookup[_concept] = {
        "frequency": _row["Evidence Frequency"],
        "justification": _row["Justification"],
    }

# Class列表不再手写,直接从本体文件里提取全部owl:Class,按rdfs:label取名字
ONTOLOGY_CLASSES = [
    str(_g_schema.value(c, RDFS.label))
    for c in _g_schema.subjects(RDF.type, OWL.Class)
]

for cls_name in ONTOLOGY_CLASSES:
    cls_uri = NS[cls_name]
    comment = _g_schema.value(cls_uri, RDFS.comment)

    related_properties = []
    for p, _, o in _g_schema.triples((None, RDFS.domain, cls_uri)):
        prop_label = _g_schema.value(p, RDFS.label)
        range_uri = _g_schema.value(p, RDFS.range)
        range_label = short(range_uri) if range_uri else "?"
        related_properties.append(f"{prop_label} \u2192 {range_label} (as domain)")
    for p, _, o in _g_schema.triples((None, RDFS.range, cls_uri)):
        prop_label = _g_schema.value(p, RDFS.label)
        domain_uri = _g_schema.value(p, RDFS.domain)
        domain_label = short(domain_uri) if domain_uri else "?"
        related_properties.append(f"{domain_label} \u2192 {prop_label} (as range)")

    ev = _evidence_lookup.get(cls_name, {"frequency": "N/A", "justification": "N/A"})

    demo_data["ontology_browser"].append({
        "class_name": cls_name,
        "definition": str(comment) if comment else "(no definition found)",
        "related_properties": related_properties,
        "evidence_frequency": ev["frequency"],
        "justification": ev["justification"],
    })

print(f"[OK] Ontology Browser: {len(demo_data['ontology_browser'])} 个Class的schema信息已提取\n")

# 加载经过逐条核对动词语义、真正能映射到已知Property的Stage A证据驱动问题
with open("agentcoordkg_evidence_questions.json", "r", encoding="utf-8") as f:
    evidence_questions = json.load(f)

# 每个mapped_property对应的通用SPARQL模板(复用CQ_DEFINITIONS里已经验证过的查询逻辑)
property_to_sparql = {
    "sendsMessage": ("?agent ns:sendsMessage ?message .", "{agent} sends {message}."),
    "assignedTo": ("?task ns:assignedTo ?agent .", "{task} is assigned to {agent}."),
    "actsWithin": ("?agent ns:actsWithin ?environment .", "{agent} acts within {environment}."),
    "delegatesTask": ("?agent ns:delegatesTask ?task .", "{agent} delegates {task}."),
    "violatesConstraint": ("?task ns:violatesConstraint ?constraint .", "{task} violates {constraint}."),
    "resolvesConflict": ("?task ns:resolvesConflict ?conflict .", "{task} resolves {conflict}."),
}

for sc in SCENARIOS:
    g, scenario_json = build_scenario_graph(ONTOLOGY_FILE, sc["file"])
    nodes, edges = extract_nodes_edges(g, scenario_json)
    cq_results = run_cqs(g)

    # 对每一条Stage A证据驱动的问题,在当前场景KG上实际跑查询
    evidence_grounded = []
    for eq in evidence_questions:
        prop = eq["mapped_property"]
        where_clause, nl_tmpl = property_to_sparql[prop]
        sparql = f"PREFIX ns: <{NS}>\nSELECT * WHERE {{ {where_clause} }}"
        result = g.query(sparql)
        var_names = [str(v) for v in result.vars]
        rows = list(result)
        if rows:
            answers = [nl_tmpl.format(**{var_names[i]: short(row[i]) for i in range(len(var_names))})
                       for row in rows]
        else:
            answers = ["(No instance of this relation appears in this particular scenario.)"]
        evidence_grounded.append({
            "requirement_text": eq["requirement_text"],
            "proposition": eq.get("proposition", ""),
            "original_id": eq["original_id"],
            "review_source": eq.get("review_source", ""),
            "mapped_property": prop,
            "sparql": sparql,
            "answers": answers,
        })

    # Framework Coverage / Decision Tree:如果这个场景的JSON里带有
    # _mapping_decision_tree_notes(比如AutoGen-style场景),提取出来
    # 变成一张"框架原生概念 -> 映射决定"的表,不是每个场景都有这个数据
    # (Research Assistant这种手写的illustrative case本来就不基于某个
    # 真实框架,所以不会有这张表,这是预期行为,不是bug)
    framework_coverage = []
    raw_notes = scenario_json.get("_mapping_decision_tree_notes")
    if raw_notes:
        for native_concept, decision in raw_notes.items():
            framework_coverage.append({
                "native_concept": native_concept,
                "decision": decision,
            })

    demo_data["scenarios"].append({
        "name": sc["name"],
        "description": scenario_json.get("description", ""),
        "story_summary": scenario_json.get("story_summary", ""),
        "nodes": nodes,
        "edges": edges,
        "cq_results": cq_results,
        "evidence_grounded_questions": evidence_grounded,
        "framework_coverage": framework_coverage,
    })
    print(f"[OK] 场景 '{sc['name']}': {len(nodes)} 个节点, {len(edges)} 条关系, "
          f"{sum(len(c['answers']) for c in cq_results)} 条固定CQ答案, "
          f"{len(evidence_grounded)} 条Stage A证据驱动问题, "
          f"{len(framework_coverage)} 条Framework Coverage记录")

print("\ndemo_data 构建完成,共", len(demo_data["scenarios"]), "个场景")


# ===== CELL 4: 生成HTML文件 =====

DEMO_DATA_JSON = json.dumps(demo_data, ensure_ascii=False)

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>AgentCoordKG - A Coordination Ontology for Multi-Agent LLM Systems</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; height: 100%; }
  body { font-family: -apple-system, Arial, sans-serif; background: #ffffff; color: #2c3e50; }
  h2 { margin-top: 0; color: #2c5f8a; }
  h3 { color: #7a4fc0; }
  a { color: #2a7fc4; }

  .app-shell { display: flex; height: 100vh; }

  /* Left progress-bar style navigation */
  .sidebar { width: 240px; flex-shrink: 0; background: #f5f7fa; border-right: 1px solid #dde3e8;
    padding: 24px 0; overflow-y: auto; }
  .sidebar .brand { font-weight: bold; color: #2c5f8a; font-size: 16px; padding: 0 20px 20px 20px; }
  .step { position: relative; padding: 10px 20px 10px 36px; cursor: pointer; font-size: 14px;
    color: #4a5a68; border-left: 3px solid transparent; }
  .step:hover { background: #eef2f6; color: #2c5f8a; }
  .step.active { background: #e8eef4; color: #2c5f8a; font-weight: bold; border-left: 3px solid #2c5f8a; }
  .step::before { content: ""; position: absolute; left: 14px; top: 15px; width: 9px; height: 9px;
    border-radius: 50%; background: #ccd4da; }
  .step.active::before { background: #2c5f8a; }
  .step-line { position: absolute; left: 18px; top: 26px; width: 1px; height: calc(100% - 4px);
    background: #dde3e8; }
  .scenario-sublist { margin-left: 16px; border-left: 1px dashed #ccd4da; }
  .scenario-item { padding: 7px 12px 7px 20px; cursor: pointer; font-size: 12.5px; color: #5a6a75; }
  .scenario-item:hover { color: #2c5f8a; background: #eef2f6; }
  .scenario-item.active { color: #2c5f8a; font-weight: bold; background: #e8eef4; }
  .sidebar .step[data-nolink="github"] { margin-top: 8px; border-top: 1px solid #dde3e8; padding-top: 16px; }

  /* Main content area: one page visible at a time */
  .content-area { flex: 1; overflow-y: auto; padding: 40px 48px; }
  .page { display: none; max-width: 1100px; }
  .page.active { display: block; }
  .lede { color: #5a6a75; font-size: 14px; line-height: 1.6; max-width: 760px; }

  select { font-size: 14px; padding: 4px 8px; background: #ffffff; color: #2c3e50;
    border: 1px solid #ccd4da; border-radius: 4px; }

  #graph { width: 100%; height: 72vh; min-height: 500px; border: 1px solid #ccd4da;
    background: #fbfcfd; border-radius: 6px; }
  #detail-panel { background: #fbfcfd; border: 1px solid #ccd4da; border-radius: 6px;
    padding: 10px 14px; margin-top: 10px; font-size: 13px; min-height: 20px; }
  .answer { margin-top: 6px; padding: 6px 8px; background: #f0f8ec; border-left: 3px solid #6ab04c;
    font-size: 13px; color: #2c3e2c; }
  #description { color: #5a6a75; font-size: 13px; margin: 10px 0 16px 0; }
  .citation-tag { display: inline-block; margin-top: 4px; padding: 2px 6px; background: #ffe8b3;
    color: #6b4f1a; border-radius: 3px; font-size: 12px; }

  .evidence-btn { display: block; width: 100%; text-align: left; margin: 4px 0; padding: 6px 10px;
    background: #f5f0fb; border: 1px solid #c9a9e6; color: #5a3d78; border-radius: 4px;
    cursor: pointer; font-size: 12px; }
  .evidence-btn:hover { background: #ecdcf7; }
  .evidence-source { margin-top: 6px; padding: 6px 8px; background: #faf8fc; border-left: 3px solid #9b59b6;
    font-size: 12px; color: #4a4a4a; }

  .class-card { border: 1px solid #dde3e8; border-radius: 6px; padding: 10px; margin: 8px 0;
    background: #fbfcfd; }
  .class-name { font-weight: bold; font-size: 15px; color: #2c5f8a; }
  .class-meta { font-size: 12px; color: #5a6a75; margin-top: 4px; }
  .class-props { font-size: 12px; color: #2c3e50; margin-top: 6px; }
  .evidence-freq-tag { display: inline-block; margin-top: 6px; padding: 2px 6px; background: #d6eaf8;
    border-radius: 3px; font-size: 11px; color: #1b4f72; }
  .sparql-block { margin-top: 6px; padding: 8px; background: #2d2d2d; color: #e0e0e0; border-radius: 4px;
    font-family: 'Courier New', monospace; font-size: 11px; white-space: pre-wrap; overflow-x: auto;
    border: 1px solid #444; }
  table.coverage-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12px; }
  table.coverage-table th, table.coverage-table td { border: 1px solid #dde3e8; padding: 6px 8px;
    text-align: left; vertical-align: top; color: #2c3e50; }
  table.coverage-table th { background: #f5f7fa; color: #2c5f8a; }
  #coverage-empty { font-size: 12px; color: #8a97a0; font-style: italic; margin-top: 8px; }

  .cq-card { border: 1px solid #dde3e8; border-radius: 8px; padding: 16px; margin: 16px 0; background: #fbfcfd; }
  .cq-card h4 { margin: 0 0 6px 0; color: #2c5f8a; }
  .cq-purpose { font-size: 13px; color: #5a6a75; margin-bottom: 10px; }
  .cq-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #8a97a0; margin-top: 10px; }
  .nl-template-block { margin-top: 4px; padding: 8px; background: #f5f0fb; color: #5a3d78; border-radius: 4px;
    font-family: 'Courier New', monospace; font-size: 12px; border: 1px solid #c9a9e6; }

  details.evidence-details { margin-top: 24px; }
  details.evidence-details summary { cursor: pointer; font-size: 13px; color: #7a4fc0; font-weight: bold; }
</style>
</head>
<body>

<div class="app-shell">
  <nav class="sidebar">
    <div class="brand">AgentCoordKG</div>
    <div class="step" data-page="about">About</div>
    <div class="step" data-page="schema">Ontology Schema</div>
    <div class="step" data-page="usecases">Use Cases &amp; Competency Questions</div>
    <div class="step" data-page="demo">Prototype Demo</div>
    <div class="scenario-sublist" id="scenario-sublist"></div>
    <a class="step" data-nolink="github" href="https://github.com/" target="_blank">GitHub Project &#8599;</a>
  </nav>

  <main class="content-area">

    <div class="page" id="page-about">
      <h2>About AgentCoordKG</h2>
      <p class="lede">
        AgentCoordKG is an evidence-driven ontology for multi-agent LLM coordination -
        delegation, messaging, conflict, and constraint-governed task resolution.
        It is derived from 6 independent literature reviews (188 unique citations) and
        validated against the documented native schemas of five production agent
        frameworks (CrewAI, AutoGen, LangGraph, MetaGPT, and the OpenAI Agents SDK).
        It shares its Agent, Environment, and Decision concepts with a companion
        ontology, HarnessKG, which addresses knowledge provenance and memory rather
        than coordination.
      </p>
    </div>

    <div class="page" id="page-schema">
      <h2>Ontology Schema</h2>
      <p class="lede">
        The schema below describes AgentCoordKG on its own terms - Classes, their
        definitions, the Properties attached to them, and how much literature support
        each one has - independent of any scenario or instance data.
      </p>
      <div id="ontology-class-list"></div>
    </div>

    <div class="page" id="page-usecases">
      <h2>Use Cases &amp; Competency Questions</h2>
      <p class="lede">
        AgentCoordKG's design was guided by a set of Competency Questions (CQs) -
        concrete explanatory needs a coordinator or auditor would have when inspecting
        a multi-agent execution trace. Below, each CQ is presented with its purpose,
        the SPARQL query used to answer it, and the natural-language template used to
        render the raw query result as a human-readable explanation.
      </p>
      <div id="cq-explainer-list"></div>
    </div>

    <div class="page" id="page-demo">
      <h2 id="demo-scenario-title">Prototype Demo</h2>
      <div id="description"></div>

      <p style="font-size:12px;color:#5a6a75;margin-bottom:6px;">
        <strong>Tip:</strong> Click any node below to see its definition and evidence
        source. Use the <strong>+</strong> / <strong>−</strong> buttons (or scroll) to
        zoom, and drag to reposition the view.
      </p>
      <div style="position:relative;">
        <div id="graph"></div>
        <div id="zoom-controls" style="position:absolute; top:10px; right:10px; display:flex; flex-direction:column; gap:4px; z-index:5;">
          <button id="zoom-in-btn" style="width:32px;height:32px;font-size:18px;font-weight:bold;background:#ffffff;border:1px solid #ccd4da;border-radius:4px;cursor:pointer;color:#2c5f8a;">+</button>
          <button id="zoom-out-btn" style="width:32px;height:32px;font-size:18px;font-weight:bold;background:#ffffff;border:1px solid #ccd4da;border-radius:4px;cursor:pointer;color:#2c5f8a;">−</button>
        </div>
      </div>
      <div id="detail-panel"><em>Click a node in the graph to see its definition and evidence source.</em></div>

      <h3 style="margin-top:28px;">Framework Coverage - Existing-KG Decision Tree</h3>
      <p class="lede" style="font-size:12px;">
        This table is the direct companion to the Knowledge Graph above: for scenarios
        built from a real framework's documented data schema (e.g. CrewAI), it lists
        every native concept from that framework alongside our explicit disposition of
        it - does it land on one of AgentCoordKG's locked Classes/Properties, or is it
        out of scope? This is the audit trail behind the generalizability claim.
      </p>
      <div id="coverage-content"></div>

      <details class="evidence-details">
        <summary>Ask a Question Grounded in Literature Evidence</summary>
        <p class="lede" style="font-size:12px;">
          Nothing below was authored by us. Each item is a natural-language requirement
          that a human/LLM extraction pipeline pulled directly from the underlying
          literature corpus. Clicking an item reveals where it came from and what it
          returns when queried against this scenario's Knowledge Graph.
        </p>
        <div id="evidence-buttons"></div>
        <div id="evidence-answer"></div>
      </details>
    </div>

  </main>
</div>

<script>
const demoData = __DEMO_DATA__;
let network = null;
let currentScenarioIdx = 0;

function showPage(pageId) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById("page-" + pageId).classList.add("active");
  document.querySelectorAll(".step").forEach(s => s.classList.remove("active"));
  const stepEl = document.querySelector('.step[data-page="' + pageId + '"]');
  if (stepEl) stepEl.classList.add("active");

  // Redraw the network on demo page in case it was sized while hidden (display:none
  // gives a zero-size canvas to vis-network, so we must re-fit after becoming visible).
  if (pageId === "demo" && network) {
    setTimeout(() => { network.redraw(); network.fit(); }, 50);
  }
}

function renderCQExplainers() {
  const listDiv = document.getElementById("cq-explainer-list");
  listDiv.innerHTML = "";
  const sample = demoData.scenarios[0].cq_results;
  sample.forEach(cq => {
    const card = document.createElement("div");
    card.className = "cq-card";
    let html = "<h4>" + cq.cq_id + ": " + cq.question + "</h4>";
    html += "<div class='cq-purpose'>" + cq.purpose + "</div>";
    html += "<div class='cq-label'>SPARQL Query</div>";
    html += "<div class='sparql-block'>" + cq.sparql.replace(/</g, "&lt;") + "</div>";
    html += "<div class='cq-label'>Natural Language Template</div>";
    html += "<div class='nl-template-block'>" + cq.nl_template_raw.replace(/</g, "&lt;") + "</div>";
    card.innerHTML = html;
    listDiv.appendChild(card);
  });
}

function loadScenario(idx) {
  currentScenarioIdx = idx;
  const sc = demoData.scenarios[idx];
  document.getElementById("demo-scenario-title").innerText = "Prototype Demo: " + sc.name;
  const storySummary = sc.story_summary || sc.description;
  document.getElementById("description").innerHTML =
    "<strong>What's happening in this scenario:</strong> " + storySummary;

  document.querySelectorAll(".scenario-item").forEach(el => el.classList.remove("active"));
  const activeItem = document.querySelector('.scenario-item[data-idx="' + idx + '"]');
  if (activeItem) activeItem.classList.add("active");

  const nodes = new vis.DataSet(sc.nodes.map(n => ({
    id: n.id, label: n.label, group: n.group, title: n.group
  })));
  const edges = new vis.DataSet(sc.edges.map(e => ({
    from: e.from, to: e.to, label: e.label, arrows: "to", font: {align: "top", size: 16}
  })));

  const container = document.getElementById("graph");
  const data = { nodes, edges };
  const options = {
    groups: {
      Agent: {color: {background: "#4dd0c4", border: "#2a9d94"}, font: {color: "#0d1117"}},
      Task: {color: {background: "#a875e8", border: "#7a4fc0"}, font: {color: "#0d1117"}},
      Message: {color: {background: "#7fc8f0", border: "#4a9ec8"}, font: {color: "#0d1117"}},
      Decision: {color: {background: "#ffd88a", border: "#d6a94a"}, font: {color: "#0d1117"}},
      Conflict: {color: {background: "#f08a8a", border: "#c85a5a"}, font: {color: "#0d1117"}},
      Constraint: {color: {background: "#b0b8c0", border: "#7a8590"}, font: {color: "#0d1117"}},
      Environment: {color: {background: "#8ae0a0", border: "#4ab06a"}, font: {color: "#0d1117"}}
    },
    physics: {
      stabilization: true,
      barnesHut: { springLength: 200, avoidOverlap: 0.9 }
    },
    nodes: { font: {size: 28, color: "#1a1a1a"}, margin: 14, size: 24 },
    edges: {font: {size: 18, color: "#2c3e50", strokeWidth: 6, strokeColor: "#ffffff"}, color: {color: "#8a97a0"}, width: 2}
  };
  network = new vis.Network(container, data, options);

  network.once("stabilizationIterationsDone", function () {
    network.setOptions({ physics: false });
    network.fit();
  });

  document.getElementById("zoom-in-btn").onclick = () => {
    const scale = network.getScale();
    network.moveTo({ scale: scale * 1.2 });
  };
  document.getElementById("zoom-out-btn").onclick = () => {
    const scale = network.getScale();
    network.moveTo({ scale: scale / 1.2 });
  };

  network.on("click", function(params) {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0];
      const nodeInfo = sc.nodes.find(n => n.id === nodeId);
      let html = "<strong>" + nodeInfo.label + "</strong> (" + nodeInfo.group + ")";
      html += "<p>" + nodeInfo.definition + "</p>";
      if (nodeInfo.citation) {
        html += "<span class='citation-tag'>Evidence: " + nodeInfo.citation + "</span>";
      }
      document.getElementById("detail-panel").innerHTML = html;
    }
  });

  const evidenceButtonsDiv = document.getElementById("evidence-buttons");
  evidenceButtonsDiv.innerHTML = "";
  sc.evidence_grounded_questions.forEach((eq) => {
    const btn = document.createElement("button");
    btn.className = "evidence-btn";
    btn.innerText = "\\"" + eq.proposition + "\\"";
    btn.onclick = () => {
      let html = "<div class='evidence-source'>";
      html += "<strong>Original Citation:</strong> " + eq.original_id;
      if (eq.review_source) { html += " (" + eq.review_source + ")"; }
      html += "<br><strong>Extracted Proposition (S-R-O):</strong> " + eq.proposition;
      html += "<br><strong>Ontology Requirement:</strong> \\"" + eq.requirement_text + "\\"";
      html += "<br><strong>Mapped ontology relation:</strong> " + eq.mapped_property;
      html += "</div>";
      html += eq.answers.map(a => "<div class='answer'>" + a + "</div>").join("");
      html += "<div class='sparql-block'>" + eq.sparql.replace(/</g, "&lt;") + "</div>";
      document.getElementById("evidence-answer").innerHTML = html;
    };
    evidenceButtonsDiv.appendChild(btn);
  });
  document.getElementById("evidence-answer").innerHTML = "";

  const coverageDiv = document.getElementById("coverage-content");
  if (sc.framework_coverage && sc.framework_coverage.length > 0) {
    let html = "<table class='coverage-table'><tr><th>Native Framework Concept</th><th>Mapping Decision</th></tr>";
    sc.framework_coverage.forEach(row => {
      html += "<tr><td>" + row.native_concept + "</td><td>" + row.decision + "</td></tr>";
    });
    html += "</table>";
    coverageDiv.innerHTML = html;
  } else {
    coverageDiv.innerHTML = "<div id='coverage-empty'>This scenario is a hand-authored illustrative case, " +
      "not modeled on a specific external framework's native schema - no coverage table applies. " +
      "(Select any of the framework-named scenarios for a worked example of framework coverage analysis.)</div>";
  }
}

function renderOntologyBrowser() {
  const listDiv = document.getElementById("ontology-class-list");
  listDiv.innerHTML = "";
  demoData.ontology_browser.forEach((cls) => {
    const card = document.createElement("div");
    card.className = "class-card";
    let html = "<div class='class-name'>" + cls.class_name + "</div>";
    html += "<div class='class-meta'>" + cls.definition + "</div>";
    if (cls.related_properties.length > 0) {
      html += "<div class='class-props'><strong>Properties:</strong> " + cls.related_properties.join("; ") + "</div>";
    }
    html += "<div class='evidence-freq-tag'>Evidence: " + cls.evidence_frequency + "</div>";
    card.innerHTML = html;
    listDiv.appendChild(card);
  });
}

// Build the sidebar's scenario sub-list under "Prototype Demo"
const sublistDiv = document.getElementById("scenario-sublist");
demoData.scenarios.forEach((sc, i) => {
  const item = document.createElement("div");
  item.className = "scenario-item";
  item.setAttribute("data-idx", i);
  item.innerText = sc.name;
  item.onclick = () => {
    loadScenario(i);
    showPage("demo");
  };
  sublistDiv.appendChild(item);
});

// Top-level step navigation click handlers
document.querySelectorAll(".step[data-page]").forEach(step => {
  step.onclick = () => showPage(step.getAttribute("data-page"));
});

renderOntologyBrowser();
renderCQExplainers();
loadScenario(0);
showPage("about");
</script>
</body>
</html>
"""

html_output = HTML_TEMPLATE.replace("__DEMO_DATA__", DEMO_DATA_JSON)

with open("agentcoordkg_demo.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("已生成 agentcoordkg_demo.html")


# ===== CELL 5: 在Colab里直接预览 =====
# from IPython.display import HTML
# with open("agentcoordkg_demo.html", encoding="utf-8") as f:
#     display(HTML(f.read()))


# ===== CELL 6: 下载文件(之后可以部署到GitHub Pages) =====
# from google.colab import files
# files.download("agentcoordkg_demo.html")
