# Skylark Drones — Decision Log

## 1. Key assumptions

1. The two supplied datasets will be imported into separate monday.com boards named/identified as Deals and Work Orders.
2. The agent receives read-only access to those boards.
3. Board IDs and an API token can be supplied through deployment secrets.
4. Because the assignment does not prescribe exact column names, the prototype maps common business concepts using normalized/fuzzy aliases.
5. Pipeline value is calculated only from populated numeric amount/value fields.
6. Missing values are excluded from calculations rather than silently treated as zero.
7. “This quarter” means the current calendar quarter when a date range is needed.
8. Revenue is only reported when the board contains a usable revenue/amount field; the agent does not invent a revenue definition.

## 2. Trade-offs

### Streamlit over a custom React + API stack
Streamlit gives a conversational UI and deployment-ready prototype quickly, which is appropriate for the six-hour constraint. A production system would likely separate frontend and backend.

### LLM for planning, Python for calculations
The LLM interprets founder language and creates a structured plan. Numerical calculations happen deterministically from live Monday data. This reduces hallucination risk.

### Runtime schema discovery
The agent reads board columns from Monday and maps likely fields instead of hardcoding the sample spreadsheet structure. This makes the prototype more resilient to messy imports.

### Full-board read with cursor pagination
For the assignment's expected scale, this is simple and transparent. For production, server-side filters and caching should reduce latency and API usage.

## 3. Data resilience

The prototype:
- handles null/blank values,
- normalizes text for matching,
- accepts several common date formats,
- parses currency-like numeric strings,
- reports missing recognized fields,
- reports columns that were not recognized,
- avoids treating missing amounts as zero.

## 4. Query understanding

The preferred path uses an LLM to convert a natural-language question into:
- metric,
- sector,
- start date,
- end date,
- clarification requirement.

If no LLM key is configured, a deterministic fallback handles common queries such as pipeline + sector.

## 5. Leadership updates interpretation

“The agent should help prepare data for leadership updates” is implemented as a dedicated **Generate leadership update** action. It produces a concise executive view covering:
- pipeline,
- operations,
- risks/data quality,
- suggested focus.

The update is generated from live Monday.com data rather than a static report.

## 6. What I would do with more time

1. Add server-side Monday filters and caching.
2. Add richer semantic mapping using the actual imported schemas.
3. Add explicit revenue recognition and forecast definitions agreed with Skylark.
4. Add a persistent query/audit log.
5. Add authentication for the hosted prototype.
6. Add charts and drill-down tables.
7. Add automated tests using anonymized fixture data.
8. Add a production database/cache for large boards.
