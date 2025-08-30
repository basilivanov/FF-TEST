
# Analysis of Duplicates and Conflicts

This report identifies clusters of documents that are either duplicates, different versions of the same concept, or closely related and should be cross-referenced.

---

## Cluster 1: E2E Test Runbooks

**Files:**
- `/opt/feature-factory/runbook_E12_E2E_TEST_v2.md` (SHA: 4651e5...)
- `/opt/feature-factory/runbook_E12_E2E_TEST.md` (SHA: fb367e...)

**Analysis:**
These two files represent two versions of the E2E test runbook. The `v2` version appears to be a more concise summary, while the other is a detailed, step-by-step guide with full `curl` commands.

**Proposal: `MERGE`**
- **Action:** Merge the detailed commands from the original runbook as a collapsible `<details>` section or an appendix within the `v2` runbook.
- **Rationale:** This will create a single, authoritative runbook that contains both a high-level summary and the detailed implementation, reducing confusion and the need to maintain two separate documents.
- **Ownership:** The `QA` or `DevOps` role should be responsible for this merge.

---

## Cluster 2: Agent Charters and Prompts

**Files:**
- `/opt/feature-factory/agents/charters/architect.md` and `/opt/feature-factory/agents/prompts/architect.md`
- `/opt/feature-factory/agents/charters/dev.md` and `/opt/feature-factory/agents/prompts/dev.md`
- `/opt/feature-factory/agents/charters/maintainer.md` and `/opt/feature-factory/agents/prompts/maintainer.md`
- `/opt/feature-factory/agents/charters/qa.md` and `/opt/feature-factory/agents/prompts/qa.md`
- `/opt/feature-factory/agents/charters/scribe.md` and `/opt/feature-factory/agents/prompts/scribe.md`

**Analysis:**
For each agent role, there is a `charter` document (defining the role's purpose, inputs, outputs, and constraints) and a `prompt` document (defining the persona and direct instructions for the LLM). While not direct duplicates, their content is highly coupled.

**Proposal: `REVIEW for consistency`**
- **Action:** No merge is proposed at this time. However, a formal review process should be established to ensure that the `prompt` for each role is a direct and accurate implementation of its corresponding `charter`.
- **Rationale:** Any drift between the charter and the prompt can lead to the agent behaving in ways not aligned with the system's architecture. Keeping them separate allows for a formal definition (charter) and a flexible implementation (prompt), but requires a consistency check.
- **Ownership:** The `Architect` role should be responsible for this review.

---

## Cluster 3: Gate Policies

**Files:**
- `/opt/feature-factory/docs/ChangePolicy-Gate-001.md` (Title: "Gate Policy — причины REJECT")
- `/opt/feature-factory/docs/Gate-Rules-Roles.md` (Title: "Правила Gate для ролей/промптов")

**Analysis:**
Both documents describe the `Gate` mechanism. `ChangePolicy-Gate-001.md` focuses on a list of generic REJECT codes, while `Gate-Rules-Roles.md` defines more specific rules and required fields for each agent's output.

**Proposal: `CROSS-REFERENCE`**
- **Action:** Add links at the top of each document pointing to the other.
- **Rationale:** These documents are complementary. A developer or architect debugging a `Gate` rejection would benefit from having easy access to both the generic codes and the role-specific rules to quickly diagnose the issue.
- **Ownership:** The `Scribe` role should be tasked with adding the cross-references.
