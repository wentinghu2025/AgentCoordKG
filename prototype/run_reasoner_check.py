"""
run_reasoner_check.py

对给定的Schema文件和(可选的)带实例数据文件,分别运行HermiT DL Reasoner,
检查逻辑一致性。这是Evaluation部分"Ontology Consistency"这一项的可复现来源。

依赖:
  pip install owlready2 --break-system-packages
  需要系统有Java(owlready2内置的HermiT.jar依赖Java运行)

用法:
  python3 run_reasoner_check.py --schema HarnessKG.ttl --instances HarnessKG_with_instances.ttl
  python3 run_reasoner_check.py --schema AgentCoordKG.ttl --instances AgentCoordKG_with_instances.ttl

命名空间会自动从Schema文件本身推断,不需要手动指定
(这样同一份脚本对HarnessKG/AgentCoordKG都能正确工作,不需要为每个本体
单独改一份脚本或写死命名空间——这是2026-07-18修复的一个真实bug,
之前命名空间写死指向harnesskg#,导致对AgentCoordKG跑该脚本时
NamedIndividual声明会被错误跳过)。
"""

import argparse
import os
import rdflib
from rdflib import Graph, RDF, OWL
from owlready2 import get_ontology, sync_reasoner_hermit, default_world


def infer_ontology_namespace(g):
    """从图里第一个owl:Class的URI推断命名空间,不写死。"""
    for cls in g.subjects(RDF.type, OWL.Class):
        ns = str(cls)
        if "#" in ns:
            return ns.rsplit("#", 1)[0] + "#"
    raise ValueError("无法从本体文件里推断出命名空间——请确认文件至少定义了一个owl:Class")


def prepare_for_owlready2(ttl_path, out_path):
    """
    owlready2对RDF/XML的解析,要求实例显式声明owl:NamedIndividual才能被
    正确识别为Individual(即使已经有明确的Class type三元组)。这个函数
    补齐这个声明,不影响原始.ttl文件或SPARQL查询流程,只用于Reasoner检查。
    """
    g = Graph()
    g.parse(ttl_path, format="turtle")

    ns = infer_ontology_namespace(g)

    classes = set(g.subjects(RDF.type, OWL.Class))
    obj_props = set(g.subjects(RDF.type, OWL.ObjectProperty))
    data_props = set(g.subjects(RDF.type, OWL.DatatypeProperty))
    schema_uris = classes | obj_props | data_props

    added = 0
    for s, p, o in list(g.triples((None, RDF.type, None))):
        if str(o).startswith(ns) and s not in schema_uris and o in classes:
            g.add((s, RDF.type, OWL.NamedIndividual))
            added += 1

    g.serialize(destination=out_path, format="pretty-xml")
    return added


def run_check(rdf_path, label):
    print(f"\n{'='*20} {label} {'='*20}")
    onto = get_ontology("file://" + os.path.abspath(rdf_path)).load()
    individuals = list(onto.individuals())
    print(f"加载的Class数: {len(list(onto.classes()))}")
    print(f"加载的Object Property数: {len(list(onto.object_properties()))}")
    print(f"加载的Individual数: {len(individuals)}")

    with onto:
        sync_reasoner_hermit(infer_property_values=True)

    inconsistent = list(default_world.inconsistent_classes())
    if inconsistent:
        print(f"⚠ 检测到 {len(inconsistent)} 个不一致的Class: {inconsistent}")
        return False
    else:
        print("✓ 0个不一致 —— 本体逻辑一致")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, help="Schema-only .ttl文件路径")
    parser.add_argument("--instances", default=None,
                         help="带实例数据的.ttl文件路径(可选,不传则只做Schema检查)")
    args = parser.parse_args()

    prepare_for_owlready2(args.schema, "_schema_for_reasoner.rdf")
    ok1 = run_check("_schema_for_reasoner.rdf", f"Schema Only Consistency Check ({args.schema})")

    ok2 = None
    if args.instances:
        prepare_for_owlready2(args.instances, "_instances_for_reasoner.rdf")
        ok2 = run_check("_instances_for_reasoner.rdf",
                         f"Schema + Instance Data Consistency Check ({args.instances})")

    print(f"\n{'='*50}")
    summary = f"Schema Only = {'PASS' if ok1 else 'FAIL'}"
    if ok2 is not None:
        summary += f", Schema+Instances = {'PASS' if ok2 else 'FAIL'}"
    print(f"最终结果: {summary}")
