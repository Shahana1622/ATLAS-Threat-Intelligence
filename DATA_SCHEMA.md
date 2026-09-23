# Data Schema

The dataset is a JSON object with `data_origin: "synthetic"` and arrays named
`actors`, `personas`, `handles`, `marketplaces`, `forums`, `pgp_identifiers`,
`wallet_identifiers`, `infrastructure`, `posts`, `behavioral_events`,
`evidence`, `relationships`, and `sources`.

All identifiers are fictional and stable within the dataset:
`Actor_001`, `Persona_001`, `Evidence_001`, `Handle_001`, `Wallet_001`,
`PGP_001`, `Infra_001`, and `Source_001`.

## Evidence

`evidence_id`, `actor_id`, `candidate_actor_id`, `evidence_type`, `source_id`,
`timestamp`, `reliability` (0 through 1), `independence_group`, `direction`,
`strength`, `description`, and `data_origin`.

`actor_id` and `candidate_actor_id` are nullable because evidence can be
unattributed or can describe a candidate relationship. `direction` is one of
`supports`, `contradicts`, or `contextual`.

## Relationships

`relationship_id`, `source_entity`, `target_entity`, `relationship_type`,
`strength` (0 through 1), `evidence_ids`, `timestamp`, and `data_origin`.

## Personas

`persona_id`, `actor_id`, `handles`, `writing_samples`, `behavioral_events`,
`platforms`, `first_seen`, `last_seen`, and `data_origin`.

Additional record types use the same stable identifier conventions and carry
timestamps or source references where applicable.

## Investigator views

Module E responses carry `data_origin: "synthetic"`. Graph edges retain the
foundation relationship `evidence_ids`. Actor views include independent
evidence-group counts, supporting/conflicting evidence, and a synthetic
attribution hypothesis flag. Audit events use deterministic `Audit_NNN`
identifiers and include action, entity IDs, evidence IDs, and parameters.
CAS output is a deterministic investigator explanation in this checkout, not a
statistical guarantee and not an identity conclusion.

