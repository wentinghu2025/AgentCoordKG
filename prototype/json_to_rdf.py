"""
json_to_rdf.py

把 research_assistant_case.json 里的实例和关系,转换成RDF三元组,
合并进 HarnessKG.ttl 已有的本体(Class/Property定义),输出一个
完整的、既有Schema又有实例数据的 .ttl 文件。

关于溯源(Evidence Traceability)的设计:
  每一个 derivedFromCitation 字段的值(比如 "H29"),不是简单地作为
  一个文本属性贴在实例上,而是被建成一个独立的 RDF个体(:Citation_H29,
  类型为 :Citation)。这样后面SPARQL可以直接做关联查询,比如
  "有哪些实例来自citation H29" ——这是一个真正的图连接查询,
  不是字符串匹配。

  注意::Citation 这个类是Prototype层面的"证据溯源工具类",
  不是M2锁定的7个Core Domain Class之一,不需要因为加了它就去改
  M2文件或HarnessKG.ttl的本体定义部分——它只在这个实例数据层面
  出现,专门用来支撑Evidence Traceability这条查询能力。

用法:
  python3 json_to_rdf.py
  (默认读取同目录下的 HarnessKG.ttl 和 research_assistant_case.json,
   输出 HarnessKG_with_instances.ttl)
"""

import json
import argparse
import rdflib
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from rdflib.namespace import XSD

PROV = Namespace("http://www.w3.org/ns/prov#")


def infer_ontology_namespace(g):
    """
    自动从已加载的本体图里,提取它真正使用的命名空间(而不是写死一个固定值)。
    做法:找到图里第一个 owl:Class 的URI,取它的命名空间部分。
    这样同一个脚本对HarnessKG.ttl和AgentCoordKG.ttl都能正确工作,
    不需要为每个本体单独写一份脚本或手动传命名空间参数。
    """
    for cls in g.subjects(RDF.type, __import__("rdflib").namespace.OWL.Class):
        ns = str(cls)
        if "#" in ns:
            return Namespace(ns.rsplit("#", 1)[0] + "#")
    raise ValueError("无法从本体文件里推断出命名空间——请确认文件至少定义了一个owl:Class")


def load_json_scenario(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 找不到JSON场景文件 '{path}'")
        raise SystemExit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON文件 '{path}' 格式不正确 -- {e}")
        raise SystemExit(1)


def build_graph(ontology_path, json_path):
    g = Graph()
    try:
        g.parse(ontology_path, format="turtle")
    except FileNotFoundError:
        print(f"错误: 找不到本体文件 '{ontology_path}'")
        raise SystemExit(1)

    NS = infer_ontology_namespace(g)
    g.bind("ns", NS)
    g.bind("prov", PROV)

    n_triples_before = len(g)

    scenario = load_json_scenario(json_path)

    # 保留字段(id/type/label/derivedFromCitation),其余全部当作
    # 该实例的Datatype Property通用处理,不再只认memoryType这一个特例
    RESERVED_KEYS = {"id", "type", "label", "derivedFromCitation"}

    # 先建好所有涉及到的Citation个体(去重),类型标注为 :Citation
    citation_ids = set()
    for inst in scenario["instances"]:
        if "derivedFromCitation" in inst:
            citation_ids.add(inst["derivedFromCitation"])

    for cit_id in citation_ids:
        cit_uri = NS["Citation_" + cit_id]
        g.add((cit_uri, RDF.type, NS.Citation))
        g.add((cit_uri, RDFS.label, Literal(cit_id)))

    # 建每个实例:rdf:type + rdfs:label + 其余字段全部当Datatype Property + 溯源关系
    for inst in scenario["instances"]:
        inst_uri = NS[inst["id"]]
        g.add((inst_uri, RDF.type, NS[inst["type"]]))
        if "label" in inst:
            g.add((inst_uri, RDFS.label, Literal(inst["label"])))
        for key, value in inst.items():
            if key in RESERVED_KEYS:
                continue
            g.add((inst_uri, NS[key], Literal(value, datatype=XSD.string)))
        if "derivedFromCitation" in inst:
            cit_uri = NS["Citation_" + inst["derivedFromCitation"]]
            g.add((inst_uri, PROV.wasDerivedFrom, cit_uri))

    # 建关系(Object Property三元组)
    for rel in scenario["relations"]:
        s = NS[rel["subject"]]
        p = NS[rel["property"]]
        o = NS[rel["object"]]
        g.add((s, p, o))

    n_triples_after = len(g)
    print(f"本体原有三元组: {n_triples_before}")
    print(f"加入实例数据后共: {n_triples_after} (新增 {n_triples_after - n_triples_before})")
    print(f"共建立 {len(citation_ids)} 个Citation个体: {sorted(citation_ids)}")

    return g


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="把JSON场景数据转换成RDF,合并进已有本体,输出带实例数据的.ttl文件"
    )
    parser.add_argument("--ontology", default="HarnessKG.ttl",
                         help="本体schema文件路径(默认: HarnessKG.ttl)")
    parser.add_argument("--json", dest="json_path", default="research_assistant_case.json",
                         help="JSON场景数据文件路径(默认: research_assistant_case.json)")
    parser.add_argument("--output", default="HarnessKG_with_instances.ttl",
                         help="输出文件路径(默认: HarnessKG_with_instances.ttl)")
    args = parser.parse_args()

    g = build_graph(args.ontology, args.json_path)
    try:
        g.serialize(destination=args.output, format="turtle")
        print(f"\n已写入 {args.output}")
    except Exception as e:
        print(f"错误: 写入输出文件失败 -- {e}")
        raise SystemExit(1)
