# Stargo Weekly KPI Pack

Week: **4–8 October 2026**, Asia/Jerusalem (Sunday–Thursday).

This file was generated from persisted SQLite records by `apps/api/export_kpi.py`.

## Acquisition KPIs

| KPI | Actual | Target | Variance |
|---|---:|---:|---:|
| Qualified Leads | 6 | 25 | -19 |
| Meetings Booked | 4 | 15 | -11 |
| Meetings Held | 3 | 12 | -9 |
| Opportunities Created | 2 | 5 | -3 |

## First-touch attribution

| Source | QLs | Contact IDs |
|---|---:|---|
| event-email | 2 | HS-1001, HS-1004 |
| new-connection | 1 | HS-1013 |
| organic/referral | 1 | EXT-95e4970b23835c54 |
| paid | 1 | HS-1009 |
| warm-network | 1 | HS-1017 |

## Data completeness

- `event-email`: **received**
- `historical-reactivation`: **UNKNOWN — feed not received**
- `new-connection`: **received**
- `organic/referral`: **received**
- `paid`: **received**
- `warm-network`: **received**

Unknown source feeds must not be represented as a zero count.

## Expansion (excluded from acquisition)

| Activity | Actual | Supporting event IDs |
|---|---:|---|
| Qualified Leads | 0 | — |
| Meetings Booked | 1 | PE-006 |
| Meetings Held | 0 | — |
| Opportunities Created | 0 | — |

## Traceable evidence

### Qualified Leads (6)

| Source ID | Person / contact | Timestamp | Inclusion basis |
|---|---|---|---|
| SD-001 | Pieter Claes (`HS-1004`) | 2026-10-04T10:05:00+03:00 | five QL conditions frozen at sales acceptance |
| SD-002 | Anouk de Vries (`HS-1001`) | 2026-10-05T09:40:00+03:00 | five QL conditions frozen at sales acceptance |
| SD-003 | Rachel Lim (`HS-1009`) | 2026-10-06T08:15:00+03:00 | five QL conditions frozen at sales acceptance |
| SD-007 | Tom Becker (`HS-1013`) | 2026-10-07T09:00:00+03:00 | five QL conditions frozen at sales acceptance |
| SD-008 | Yossi Mizrahi (`EXT-95e4970b23835c54`) | 2026-10-07T15:00:00+03:00 | five QL conditions frozen at sales acceptance |
| SD-009 | Noam Levi (`HS-1017`) | 2026-10-07T16:20:00+03:00 | five QL conditions frozen at sales acceptance |

### Meetings Booked (4)

| Source ID | Person / contact | Timestamp | Inclusion basis |
|---|---|---|---|
| PE-003 | HS-1004 (`HS-1004`) | 2026-10-04T10:30:00+03:00 | event timestamp within reporting week |
| PE-004 | HS-1001 (`HS-1001`) | 2026-10-05T10:00:00+03:00 | event timestamp within reporting week |
| PE-007 | HS-1009 (`HS-1009`) | 2026-10-07T05:00:00Z | event timestamp within reporting week |
| PE-010 | HS-1013 (`HS-1013`) | 2026-10-08T11:00:00+03:00 | event timestamp within reporting week |

### Meetings Held (3)

| Source ID | Person / contact | Timestamp | Inclusion basis |
|---|---|---|---|
| PE-002 | HS-1015 (`HS-1015`) | 2026-10-04T11:00:00+03:00 | event timestamp within reporting week |
| PE-005 | HS-1004 (`HS-1004`) | 2026-10-06T14:00:00+03:00 | event timestamp within reporting week |
| PE-008 | HS-1001 (`HS-1001`) | 2026-10-07T15:00:00+03:00 | event timestamp within reporting week |

### Opportunities Created (2)

| Source ID | Person / contact | Timestamp | Inclusion basis |
|---|---|---|---|
| PE-009 | HS-1015 (`HS-1015`) | 2026-10-07T17:00:00+03:00 | event timestamp within reporting week |
| PE-011 | HS-1004 (`HS-1004`) | 2026-10-08T15:00:00+03:00 | event timestamp within reporting week |

## Assumptions / boundaries

- Source attribution is the earliest inbound event for a person matched by normalized email or LinkedIn ID.
- QLs count once per person on first accepted decision date using the immutable evidence snapshot captured at that decision.
- Pipeline events are counted by their own event timestamps; existing customer events appear in expansion.
- Dates with `Z` are converted to Asia/Jerusalem before half-open window comparison.
- The synthetic seed's malformed inbound `IN-019` is quarantined, not silently made into a lead.
- The exported pack represents the local database at export time and may differ from the pristine submitted sample if operator decisions were recorded.

## Note to CRO

This reporting week delivered 6 against 25 (shortfall 19) QLs, 4 against 15 (shortfall 11) meetings booked, 3 against 12 (shortfall 9) meetings held and 2 against 5 (shortfall 3) opportunities. Unavailable feeds: historical-reactivation. The top GEO gap is 'alternatives to Laneframe for freight pricing' (score 318): low brand mentions and/or owned citations make vendor discovery less reliable. Next week, publish one human-approved, BC/PP-cited answer page for this buyer question and recapture the same prompts to measure mentions and citations.
