# Skylark Drones — Monday.com Business Intelligence Agent

## What this is

A hosted-ready conversational BI agent for the Skylark Drones technical assignment. It reads the **Deals** and **Work Orders** boards from monday.com at runtime and answers founder-level business questions.

The assignment requires dynamic monday.com reads, resilience to messy data, conversational query understanding, cross-board BI, a hosted prototype, a decision log, source code, and README. The implementation is intentionally read-only.

## Architecture

```text
Streamlit UI
    |
    v
Query Planner (OpenAI when configured; deterministic fallback)
    |
    v
Monday.com GraphQL client
    |--------------------|
    v                    v
Deals board         Work Orders board
    |                    |
    +---------+----------+
              v
      Normalization + Analytics
              |
              v
      Founder-level response
```

## Why this design

- **Streamlit:** fastest path to a polished, testable hosted prototype within a 6-hour assignment window.
- **Monday GraphQL API:** directly satisfies the read-only integration requirement.
- **Cursor pagination:** retrieves more than the first page without hardcoding sample data.
- **LLM planner:** translates natural language into a small structured query plan.
- **Deterministic analytics:** calculations are done in Python from live board data; the LLM is not trusted to calculate numbers.
- **Graceful fallback:** the app still answers basic questions if an OpenAI key is not configured.
- **Data-quality report:** recognized missing fields and unmapped columns are surfaced.

## Monday.com setup

1. Import the provided **Deal funnel Data.xlsx** into a Monday.com board named something like `Deals`.
2. Import the provided **Work_Order_Tracker Data.xlsx** into a separate board named something like `Work Orders`.
3. Keep useful column types such as:
   - Sector / Industry → text or dropdown
   - Amount / Deal Value → numbers
   - Stage / Status → status
   - Date / Close Date → date
   - Client / Customer → text
4. Create/use a Monday API token with board read access.
5. Copy each board's numeric ID.
6. Put the token and board IDs into the app sidebar or environment variables.

The app does not import or hardcode the CSV/XLSX contents.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local Streamlit URL and enter the Monday token + two board IDs.

## Replit deployment

1. Create a new Replit app from this folder.
2. Install dependencies from `requirements.txt`.
3. Set the run command to:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 3000
```

4. Deploy/publish the Replit app.
5. Configure secrets for `MONDAY_API_TOKEN`, `DEALS_BOARD_ID`, `WORK_ORDERS_BOARD_ID`, and optionally `OPENAI_API_KEY`.
6. Test the hosted URL in an incognito browser.

## Example questions

- How is our pipeline looking for energy sector this quarter?
- What are the largest deals in the current pipeline?
- Which sectors have the most pipeline value?
- How many work orders are active?
- What data quality issues should leadership know about?
- Prepare a leadership update.

## Security

- Monday credentials are supplied through environment variables or the sidebar.
- Credentials are never written to Monday boards.
- The Monday client only executes GraphQL queries.
- No Monday mutations are implemented.
- Do not commit real API keys to Git.

## Known limitations

- The exact schema of the supplied boards is unknown until they are imported into Monday.com; therefore field matching is alias/fuzzy based.
- Revenue recognition may require a business-specific definition if the Deals board does not contain a closed-won/revenue field.
- Complex joins between deals and work orders may require an explicit shared key such as client/account/project ID.
- The current prototype keeps the full board data in memory for a request; very large boards would benefit from server-side filtering, caching, and a database.
