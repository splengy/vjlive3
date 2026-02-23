# P0-INF4: Core Logic Parity Analysis

## What This Module Does

Conduct a detailed analysis of core logic components from legacy codebases (`vjlive/` and `VJlive-2/`) to identify missing implementations in VJLive3. This task focuses on the 1800+ core logic elements that form the foundation of visual effects, audio processing, and system architecture. The analysis will create a comprehensive roadmap for porting these critical components while preserving their unique characteristics.

## Public Interface

This is a planning/documentation task, not a code module. The deliverable is:

- `docs/audit/core_logic_parity_report.md` - Complete core logic parity analysis
- `docs/plans/core_logic_implementation_roadmap.md` - Detailed implementation plan
- Updates to `BOARD.md` with task breakdown

## Inputs and Outputs

**Inputs:**
- Legacy codebase 1: `/home/happy/Desktop/claude projects/vjlive/` (original vjlive)
- Legacy codebase 2: `/home/happy/Desktop/claude projects/VJlive-2/` (clean architecture reference)
- Current codebase: `VJLive3_The_Reckoning/` (target for all ports)

**Outputs:**
- Complete inventory of core logic components by category (effects, audio, system)
- Matrix showing which components exist in which codebase
- Gap analysis: components missing from VJLive3
- Porting complexity assessment (low/medium/high)
- Dependency mapping (which components depend on which systems)
- Implementation sequence optimized for minimal rework

## What It Does NOT Do

- Does NOT implement any components (this is planning only)
- Does NOT write production code
- Does NOT modify existing codebase
- Does NOT create task assignments (that's separate)

## Test Plan

Since this is a documentation task, verification is through:

1. **Completeness Check**: All core logic directories in both legacy codebases have been scanned
2. **Cross-Reference Validation**: Every component listed can be traced to actual source files in legacy codebases
3. **Stakeholder Review**: The plan must be approved by the project manager before implementation begins
4. **Consistency Check**: No duplicate entries, clear naming conventions, proper categorization

## Implementation Approach

### Phase 1: Directory Structure Analysis
- Recursively scan both legacy codebases
- Identify core logic directories: `effects/`, `audio/`, `system/`, `utils/`, etc.
- Catalog all `.py` files and their class definitions
- Extract core logic metadata from docstrings and class names

### Phase 2: Component Extraction
For each core logic file:
- Parse class names (e.g., `DepthAcidFractalDatamoshEffect`)
- Extract parameter definitions
- Identify dependencies on other modules
- Note any unique "soul" or artistic elements that must be preserved

### Phase 3: Gap Analysis
- Compare against current `src/vjlive3/core/` directory
- Mark components as: ✅ Already ported, 🔄 In progress, ⬜ Missing
- Count totals by category and phase

### Phase 4: Complexity Assessment
Rate each porting task:
- **Low**: Straightforward translation, minimal dependencies
- **Medium**: Requires adaptation to new architecture
- **High**: Significant refactoring needed, novel algorithms

### Phase 5: Roadmap Creation
- Organize missing components into implementation phases (matching BOARD.md structure)
- Create task IDs following the existing pattern (P3-VDxx, P4-AUxx, etc.)
- Sequence tasks to minimize dependencies and enable early testing
- Estimate effort per task (in days)

### Phase 6: Documentation
- Generate comprehensive markdown report with tables
- Include source references (file paths in legacy codebases)
- Add notes about special considerations for each component
- Create summary statistics

## Critical Collections Identified in BOARD.md

**Core Logic Components**: 1800+ missing implementations

**Total**: 1800+ core logic components

## Deliverables

1. `docs/audit/core_logic_parity_report.md` - Main audit report with:
   - Executive summary
   - Component inventory by category
   - Gap analysis tables
   - Complexity distribution
   - Implementation timeline estimate

2. `docs/plans/core_logic_implementation_roadmap.md` - Detailed plan with:
   - Phase 3-7 task breakdowns
   - Task IDs and descriptions
   - Source code references
   - Dependency graph
   - Risk assessment

3. Updated `BOARD.md` with:
   - All missing tasks added to appropriate phase sections
   - Proper task IDs and descriptions
   - Status set to `⬜ Todo`

4. `docs/specs/` directory populated with spec files for each high-priority task (P0 and P1 items)

## Notes

- This audit must be thorough; every component is unique and deserves bespoke treatment
- The "soul" and artistic elements of each component must be documented for preservation
- Pay special attention to audio-reactive and depth-based effects which have complex dependencies
- The output will drive the entire project timeline (20-24 weeks estimated)