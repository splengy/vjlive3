# Architecture 

**Root Reference for System Design:** [`../ARCHITECTURE.md`](../ARCHITECTURE.md)

## Context
This document serves as the Unified Memory Bank entry for system architecture. The VJLive3 project utilizes a **Hybrid Hierarchical-Cluster Swarm (HHCS)** model.

## Swarm Topology
- **Strategic Layer (Human Operator):** The User provides ultimate vision and approval.
- **Orchestration Layer (Overseer / Manager):** *Antigravity* operates as the Swarm Overseer. It manages strategic routing, writes technical specs, manages this Memory Bank, and pushes tasks to the `docs/specs/_01_todo/` queue. It DOES NOT write production implementation code.
- **Execution Layer (Workers / Sub-Agents):** Three (3) instances of *Roo Code* (local plugin, `192.168.1.50`, `192.168.1.60`) operate as the execution squads. They claim specs from the filesystem queue, write code within their sandboxed context, verify passing tests, and report back by moving specs to `docs/specs/_04_done/`.

## Network & Execution Boundaries
- Workers interact with the central orchestrator strictly via shared filesystem queues (`docs/specs/`) organized by `swarm_sync.sh`.
- The Overseer interacts with worker outputs via GitOps, filesystem synchronization, and MCP.
