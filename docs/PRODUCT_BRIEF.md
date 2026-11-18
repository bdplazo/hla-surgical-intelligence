# Product brief — discovery

## Problem, users and value
Hypothetical integration engineers onboard hospitals whose RFID messages differ in names, types and semantics. Data quality analysts investigate rejected events. A reviewer accepts mappings. Product A should make this work inspectable and reproducible. Product B is a later recommendations-only capability.

## Assumptions, not established facts
Sources provide local JSON/CSV exports; hospital identity is supplied by trusted configuration; equipment IDs can collide across hospitals; source clocks may differ; source corrections may reuse event IDs; reviewers can clarify room semantics. No actual hospital workflow has been researched or validated.

## Boundaries and minimum success
Initially prove installation and executable tooling. The future MVP must preserve raw records, quarantine invalid data, replay without duplicate history, identify conflicts and require approved mappings. No clinical decision support, patient data, external writes or claimed production deployment.

## Hypothetical metrics
Measure time to a reviewed hospital mapping, manual mapping tasks per source, validation rule coverage and minutes investigating a seeded integration error. Record baselines and repeated synthetic trials before claiming any improvement. No business impact has been measured.

## User review
The user explicitly accepted the hypothetical onboarding assumptions on 2026-11-18. They remain synthetic design assumptions, not evidence of real hospital workflows.
