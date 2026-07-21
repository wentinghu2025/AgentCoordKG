# AgentCoordKG — An Evidence-Driven Ontology for Governable Coordination in Multi-Agent LLM Systems

This repository accompanies the ISWC poster submission *"AgentCoordKG: An
Evidence-Driven Ontology for Governable Coordination in Multi-Agent LLM
Systems."* It contains the full, disclosed evidence-to-ontology pipeline:
literature extraction, canonical concept alignment, the OWL ontology
itself, a Prototype spanning 8 scenarios (including 5 modeled on real
agent frameworks' native data schemas), and all supporting evaluation
artifacts.

AgentCoordKG is a companion ontology to **HarnessKG**, sharing the same
evidence base (6 literature reviews) and methodology (Existing-KG Decision
Tree), but addressing a different concern: multi-agent *coordination and
governance* rather than *knowledge provenance and memory*. The two
ontologies share exactly three concepts — Agent, Decision, Environment —
by deliberate design; the full disclosure of this shared foundation
accompanies the poster submission itself.

## Repository Structure

```
agentcoordkg-repo/
├── ontology/           Final locked ontology (OWL/Turtle)
├── evidence/            Literature-derived, citation-grounded evaluation questions
├── prototype/           Prototype scripts, hand-authored scenarios, and the interactive HTML demo
│   ├── scenarios/        Source JSON for all 8 scenarios (3 illustrative + 5 framework-grounded)
│   └── generated/        Reproducible build outputs (RDF instance graphs)
├── figures/              Standalone Graphviz-generated figures (Cross-Framework Convergence, Ontology Schema) and their generator scripts
├── LICENSE               MIT License (code)
└── LICENSE-DATA.md       CC BY 4.0 (evidence, documentation, ontology comments)
```

## Where to Start

| If you want to... | Go to |
|---|---|
| See the final ontology (Classes/Properties) | `ontology/AgentCoordKG.ttl` |
| Try the interactive Prototype | Open `prototype/agentcoordkg_demo.html` directly in a browser (no install needed) |
| Reproduce the Knowledge Graph construction | `prototype/json_to_rdf.py` — same script used for HarnessKG; namespace is auto-inferred from the loaded ontology, so no per-ontology modification is needed |
| Reproduce the Ontology Consistency check | `prototype/run_reasoner_check.py` — requires `pip install owlready2` and a local Java runtime |
| See standalone Figures (Cross-Framework Convergence, Ontology Schema) | `figures/` |

The full write-up (Methodology, Results, Discussion, Research Questions)
accompanies the poster submission itself; this repository provides the
underlying ontology, evidence, and reproducible Prototype code.

## Validation Status (please read before reuse)

- **`ontology/AgentCoordKG.ttl`**: Fully verified — parses correctly,
  passes HermiT DL-reasoner consistency checks (schema-only and
  schema-with-instances), and all 8 Competency Questions execute correctly
  as SPARQL against every one of the 8 scenarios (64 total query
  executions).
- **`prototype/scenarios/*_case.json` (framework-grounded, 5 files)**:
  Hand-authored to match each framework's *documented* native schema
  (verified against official documentation), not extracted from live
  framework executions. Explicitly disclosed as such in each file's
  `_mapping_decision_tree_notes` field.
- **`prototype/scenarios/agentcoordkg_illustrative_case.json`,
  `agentcoordkg_trip_planning_case.json`,
  `agentcoordkg_workflow_audit_case.json`**: Hand-authored illustrative
  scenarios, not grounded in any external framework. These do not
  contribute to the Framework Coverage (Protocol Accommodation) evaluation
  metric, but do contribute to Conflict Queryability and Governance
  Completeness — see the accompanying poster submission for the full
  disclosure of why this distinction matters.
- **`evidence/agentcoordkg_evidence_questions.json`**: A small
  (6-item), strictly verb-level-checked subset of the Stage A corpus —
  disclosed as small precisely because an expanded 37-citation candidate
  pool yielded few clean instance-level matches for most properties; see
  the accompanying poster submission for the full account.

## License

- Code (`prototype/*.py`, `.html`) is released under the **MIT License**
  (see `LICENSE`).
- The evidence corpus and ontology documentation
  (`evidence/`, `.md` files throughout) are released under
  **CC BY 4.0** (see `LICENSE-DATA.md`).

## Citation

*(To be completed once the poster is finalized — placeholder for authors,
venue, and DOI/URL.)*
