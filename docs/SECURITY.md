# Security and privacy

Synthetic data only; fictional hospitals and resource IDs. No patients, real system access, external transactions or credentials. Environment files are ignored. Synthetic data does not establish GDPR compliance or certification.

Future stores and APIs must scope every read/write by hospital, enforce trusted tenant context, distinguish read and write permissions and audit approvals. SQLite on a laptop is not an authentication or tenant isolation service. A production design needs access control, retention, encryption, threat modelling, audit protection and legal review. No such controls are claimed here.

## Phase 03 local review boundary
YAML uses SafeLoader with duplicate-key rejection and strict typed configuration. Approval requires a separate explicit command and exact content hash; this is local review evidence only, without authenticated reviewer identity or tamper-resistant signature. Example YAMLs are proposals. Do not auto-approve them from an LLM or infer acceptance from simulated test reviewers. Views expose retained interpretations and are not authorization controls; scope inspection by hospital/source/mapping version. Production would need protected review records, real access control and audited migrations.

## Phase 04 boundaries
Only explicitly referenced same-hospital/source mappings with matching receipts contribute aliases. Rejected references expose a count rather than foreign-tenant mapping details. The built-in baseline treats source field names and values as data, not instructions, and cannot invoke approval, change accepted files or access hospital systems. New artifact directories prevent silent overwrite; a completion manifest distinguishes interrupted output. Optional provider injection is trusted Python code, not a sandbox; no concrete external/LLM provider exists. Approval and persisted validation remain separate commands. Read COPILOT.md for preview-only scope and known limitations.
