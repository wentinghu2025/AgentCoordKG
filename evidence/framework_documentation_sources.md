# Framework Documentation Sources

This file lists the official documentation pages consulted to verify each
framework-native concept referenced in the 5 framework-grounded scenarios
(`prototype/scenarios/*_case.json`, excluding the 3 hand-authored
illustrative scenarios) and their corresponding Existing-KG Decision Tree
judgments (`_mapping_decision_tree_notes` field in each scenario file).

All links were verified accessible as of **2026-07-24**. Framework
documentation can change over time; if a link is broken, the scenario's
`_mapping_decision_tree_notes` field still documents which native concept
was verified and what it was understood to mean at the time of writing.

## AutoGen (AG2)

- ConversableAgent reference: https://microsoft.github.io/autogen/0.2/docs/reference/agentchat/conversable_agent/
- GroupChatManager reference: https://microsoft.github.io/autogen/0.2/docs/reference/agentchat/groupchat/

Used to verify: `GroupChatManager`'s turn-order coordination (mapped to
`dependsOn`), and the escalation/authorization-limit pattern underlying
`agentcoordkg_autogen_case.json`. Note: AutoGen 0.2 is the version whose
documented schema was used; the project has since split into a community
fork (AG2, docs.ag2.ai) and a newer AutoGen 0.4+ core API.

## CrewAI

- Collaboration / `allow_delegation`: https://docs.crewai.com/en/concepts/collaboration
- Main documentation: https://docs.crewai.com/

Used to verify: `allow_delegation` (mapped to `delegatesTask`) and
`Process` (sequential task ordering, mapped to `dependsOn`), underlying
`agentcoordkg_crewai_case.json`.

## LangGraph

- Graph API overview (Node / Edge / State): https://docs.langchain.com/oss/python/langgraph/graph-api

Used to verify: `Edge` (node-to-node flow, mapped to `dependsOn`) and the
generic `Node` abstraction (the disclosed Ambiguous Design Choice: mapped
to `Agent` only when the Node wraps an LLM call), underlying
`agentcoordkg_langgraph_case.json`.

## MetaGPT

- Introduction / SOP philosophy: https://docs.deepwisdom.ai/main/en/guide/get_started/introduction.html
- Role / Action tutorials: https://github.com/geekan/MetaGPT-docs/blob/main/src/en/guide/tutorials/agent_101.md
- Multi-agent tutorial (Role _observe/_think/_act, SOP): https://github.com/geekan/MetaGPT-docs/blob/main/src/en/guide/tutorials/multi_agent_101.md

Used to verify: `SOP` (Standard Operating Procedure, mapped to
`dependsOn`) and `Role`/`Action` (mapped to `Agent`/`Task`), underlying
`agentcoordkg_metagpt_case.json`.

## OpenAI Agents SDK

- Agents overview: https://openai.github.io/openai-agents-python/agents/
- Handoffs: https://openai.github.io/openai-agents-python/handoffs/
- Guardrails: https://openai.github.io/openai-agents-python/guardrails/

Used to verify: `Handoffs` (mapped to `delegatesTask`) and `Guardrails`'
`tripwire_triggered` mechanism (interpreted as `violatesConstraint` →
`Conflict`), underlying `agentcoordkg_openai_agents_sdk_case.json`.

## How These Sources Were Used

For each framework, native concepts (e.g. AutoGen's `GroupChatManager`,
CrewAI's `allow_delegation`/`Process`, LangGraph's `Node`/`Edge`, MetaGPT's
`SOP`, OpenAI Agents SDK's `Handoffs`/`Guardrails`) were checked against
the pages above to confirm they are genuinely documented, existing
primitives -- not invented for this project. This documentation grounding
is also the basis for AgentCoordKG's central empirical finding: `dependsOn`
is independently confirmed by 4 of these 5 frameworks' distinct native
orchestration primitives (CrewAI's `Process`, AutoGen's
`GroupChatManager`, LangGraph's `Edge`, MetaGPT's `SOP`), despite each
framework using a structurally different mechanism to express task
ordering. The specific mapping decision for each concept (Direct Match /
Interpreted / Out-of-Scope / Ambiguous Design Choice) is recorded
per-scenario in each JSON file's `_mapping_decision_tree_notes` field, not
in this document.
