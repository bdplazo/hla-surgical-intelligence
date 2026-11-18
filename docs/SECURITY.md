# Security and privacy

Synthetic data only; fictional hospitals and resource IDs. No patients, real system access, external transactions or credentials. Environment files are ignored. Synthetic data does not establish GDPR compliance or certification.

Future stores and APIs must scope every read/write by hospital, enforce trusted tenant context, distinguish read and write permissions and audit approvals. SQLite on a laptop is not an authentication or tenant isolation service. A production design needs access control, retention, encryption, threat modelling, audit protection and legal review. No such controls are claimed here.
