"""Conservative alias matching; uncertain semantics always remain for human review."""

from collections import defaultdict

from hla_lab.agents.providers import SuggestionProvider
from hla_lab.agents.schemas import (
    FieldSuggestion,
    Issue,
    ProviderRequest,
    ProviderSuggestions,
    SuggestionInput,
    SuggestionOutput,
)

ALIASES = {
    "event_id": {"event_id", "id_evento"},
    "equipment_id": {"equipment_id", "tag", "dispositivo"},
    "room_id": {"room_id", "zone", "sala"},
    "event_type": {"event_type", "action", "movimiento"},
    "event_time": {"event_time", "timestamp", "fecha_hora"},
}


def propose_field_mapping(
    request: SuggestionInput, provider: SuggestionProvider | None = None
) -> SuggestionOutput:
    """Combine visible names and explicitly approved same-scope references, never guess values."""
    names = {field.name for field in request.profile.fields}
    issues = []
    known = request.known_mappings
    if any(
        k.mapping.hospital_id != request.hospital_id
        or k.mapping.source_system != request.source_system
        for k in known
    ):
        raise ValueError("Known mapping scope does not match the request")
    extra: dict[str, list[str]] = {}
    if provider is not None:
        try:
            response = ProviderSuggestions.model_validate(
                provider.propose(
                    ProviderRequest(profile=request.profile, canonical_fields=sorted(ALIASES))
                )
            )
            if not set(response.candidates).issubset(ALIASES) or any(
                not set(values).issubset(names) for values in response.candidates.values()
            ):
                raise ValueError("Provider candidates are outside the inspected schema")
            extra = response.candidates
        except Exception:  # Untrusted optional provider boundary; never expose its message/payload.
            issues.append(
                Issue(
                    code="PROVIDER_FAILED_BASELINE_USED",
                    blocking=False,
                    question="Optional provider failed; review the deterministic baseline.",
                )
            )
    suggestions, fields = [], {}
    for target, aliases in ALIASES.items():
        candidates = {name for name in names if name.casefold() in aliases}
        candidates.update(
            k.mapping.fields[target] for k in known if k.mapping.fields[target] in names
        )
        candidates.update(extra.get(target, []))
        ordered = sorted(candidates)
        status = "suggested" if len(ordered) == 1 else ("ambiguous" if ordered else "missing")
        selected = ordered[0] if len(ordered) == 1 else None
        suggestions.append(
            FieldSuggestion(target=target, candidates=ordered, selected=selected, status=status)
        )
        if selected is None:
            issues.append(
                Issue(
                    code="AMBIGUOUS_FIELD" if ordered else "MISSING_FIELD",
                    field=target,
                    blocking=True,
                    question=f"Which source field represents {target}?",
                )
            )
        else:
            fields[target] = selected
    if fields.get("event_id") != request.event_id_field:
        issues.append(
            Issue(
                code="EVENT_ID_CONFIG_MISMATCH",
                field="event_id",
                blocking=True,
                question="Confirm the event-ID field against trusted source configuration.",
            )
        )
    for target in fields:
        if sum(value == fields[target] for value in fields.values()) > 1:
            issues.append(
                Issue(
                    code="SHARED_SOURCE_FIELD",
                    field=target,
                    blocking=True,
                    question="Confirm separate source fields for distinct canonical meanings.",
                )
            )
    value_maps = {}
    for category in ("rooms", "event_types"):
        values = defaultdict(set)
        for entry in known:
            for source, target in getattr(entry.mapping, category).items():
                values[source].add(target)
        value_maps[category] = {
            source: next(iter(targets))
            for source, targets in sorted(values.items())
            if len(targets) == 1
        }
        for _source, targets in sorted(values.items()):
            if len(targets) > 1:
                issues.append(
                    Issue(
                        code="AMBIGUOUS_VALUE_ALIAS",
                        field=category,
                        blocking=True,
                        question=f"Resolve conflicting approved aliases in {category}.",
                    )
                )
        if not value_maps[category]:
            issues.append(
                Issue(
                    code="VALUE_SEMANTICS_REQUIRED",
                    field=category,
                    blocking=True,
                    question=f"Provide reviewed source-to-canonical aliases for {category}.",
                )
            )
    if any(entry.mapping.mapping_version == request.mapping_version for entry in known):
        issues.append(
            Issue(
                code="VERSION_ALREADY_KNOWN",
                blocking=True,
                question="Choose a new proposal version; do not modify an accepted version.",
            )
        )
    candidate = {
        "hospital_id": request.hospital_id,
        "source_system": request.source_system,
        "mapping_version": request.mapping_version,
        "schema_version": "1.0",
        "fields": fields,
        **value_maps,
    }
    return SuggestionOutput(candidate=candidate, fields=suggestions, issues=issues)
