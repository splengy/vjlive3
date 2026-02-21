# ADR-000: Template

## Status
Active

## Date
2026-02-20

## Context
This is the template for all Architecture Decision Records (ADRs) in the VJLive3 project. It provides a consistent structure for documenting important architectural decisions.

## Decision
Use this template for all new ADRs, following the structure and format outlined below.

## Options Considered
- **Option 1**: Use a different template format
  - Pros: Might be more concise
  - Cons: Less comprehensive, harder to follow
- **Option 2**: Use a different ADR system (e.g., external tool)
  - Pros: Might have more features
  - Cons: Adds complexity, harder to maintain
- **Option 3**: No template, free-form documentation
  - Pros: More flexible
  - Cons: Inconsistent, harder to review

## Consequences
- **Positive**: Consistent documentation, easier to review, better historical record
- **Negative**: Requires discipline to follow template
- **Neutral**: Adds overhead to decision-making process

## Related Decisions
- ADR-001: Initial Project Structure

## References
- [Architecture Decision Records](https://adr.github.io/)
- [Documenting Architecture Decisions](https://www.infoq.com/articles/documenting-architecture-decisions/)

---

## Template Structure

### Status
Current status of the ADR (Proposed/Accepted/Superseded/Deprecated/Rejected)

### Date
Date the decision was made

### Context
What is the issue or problem? Why is this decision important?

### Decision
What is the chosen solution?

### Options Considered
List of options considered with pros and cons for each

### Consequences
What are the implications of this decision?
- Positive consequences
- Negative consequences
- Neutral consequences

### Related Decisions
Links to other ADRs that are related to this decision

### References
External resources or internal documents that informed the decision

## Usage Instructions

1. Copy this template to a new file: `cp ADR_000_TEMPLATE.md ADR_001_your-decision-title.md`
2. Update the filename with the next available number and descriptive title
3. Fill in all sections with relevant information
4. Update the ADR index in `README.md`
5. Submit for review as part of your pull request

## Best Practices

- **Be concise**: Focus on essential information
- **Be objective**: Present facts, not opinions
- **Be complete**: Include all relevant context
- **Be clear**: Use clear language and structure
- **Be timely**: Create ADRs when decisions are made
- **Be collaborative**: Involve the team in the process

## Example

See `ADR_001_initial-project-structure.md` for an example of a completed ADR.