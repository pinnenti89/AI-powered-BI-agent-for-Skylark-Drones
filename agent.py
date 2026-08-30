import json, os, re, requests
from analytics import summarize

NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

def call_nvidia(prompt, api_key, model):
    """Call the NVIDIA NIM Chat Completions API with fail-safe fallback on timeout/error."""
    if not api_key:
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,
        "stream": False,
        "temperature": 0.5,
        "top_p": 0.95,
    }
    try:
        r = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=45)
        if r.status_code >= 400:
            return None
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        # On network timeout or API issues, return None to trigger instant fallback
        return None

def heuristic_plan(q):
    ql = q.lower()
    sector = None
    known_sectors = [
        "renewables", "mining", "railways", "powerline", "construction",
        "tender", "dsp", "manufacturing", "aviation", "security", "energy", "utilities"
    ]
    for s in known_sectors:
        if s in ql:
            sector = s
            break

    if "work order" in ql or "operation" in ql:
        metric = "operations"
    elif "sector" in ql:
        metric = "sector_performance"
    else:
        metric = "pipeline"

    return {
        "metric": metric,
        "sector": sector,
        "start_date": None,
        "end_date": None,
        "needs_clarification": False,
        "clarification": None,
    }

def plan_query(query, deals, work_orders, api_key, model):
    from datetime import date
    today_str = date.today().isoformat()
    prompt = f"""
You are a business intelligence query planner. Today's date is {today_str}.
Return ONLY valid JSON with keys:
metric, sector, start_date, end_date, needs_clarification, clarification.
metric must be one of: pipeline, revenue, operations, sector_performance, mixed.
Dates must be ISO YYYY-MM-DD or null.
If the user asks "this quarter" or similar relative terms, calculate start_date and end_date relative to today's date ({today_str}).
IMPORTANT: For general or high-level questions (e.g. "dashboard summary", "overview", "summary", "how are we doing", "status"), do NOT ask for clarification. Set metric to "mixed", needs_clarification to false, clarification to null, and sector/start_date/end_date to null.
User question: {query}
Available Deals board columns: {[c['title'] for c in deals['columns']]}
Available Work Orders columns: {[c['title'] for c in work_orders['columns']]}
"""
    raw = call_nvidia(prompt, api_key, model)
    if not raw:
        return heuristic_plan(query)
    try:
        raw = raw[raw.find("{"):raw.rfind("}")+1]
        return json.loads(raw)
    except Exception:
        return heuristic_plan(query)

def money(v):
    if v is None: return "n/a"
    return f"{v:,.0f}"

def clean_summary_for_llm(s):
    """Create a lightweight dict representation of summary metrics without huge row samples."""
    return {
        "deals_count": s.get("deals_count"),
        "pipeline_value": s.get("pipeline_value"),
        "average_deal_value": s.get("average_deal_value"),
        "sector_breakdown": dict(s.get("sector_breakdown", {})),
        "stage_breakdown": dict(s.get("stage_breakdown", {})),
        "work_orders_count": s.get("work_orders_count"),
        "deal_quality": s.get("deal_quality"),
        "work_order_quality": s.get("work_order_quality"),
    }

def answer_query(query, plan, deals, work_orders, api_key, model):
    s = summarize(deals, work_orders, plan)
    if s["deals_count"] == 0 and s["work_orders_count"] == 0:
        return f"I couldn't find matching records for **'{query}'**. The requested sector or date filters may have no recorded items."

    llm_payload = clean_summary_for_llm(s)
    base = f"""
Question: {query}
Plan: {json.dumps(plan)}
Computed results from live Monday.com data:
{json.dumps(llm_payload, default=str, indent=2)}
Write a founder-level answer in simple language. Include:
1) direct answer,
2) 2-4 useful insights,
3) data-quality caveats if present.
Never invent values not present in the computed results.
"""
    raw = call_nvidia(base, api_key, model)
    if raw:
        return raw

    # Dynamic query-aware fallback formatting
    sector_str = f" in **{plan.get('sector').capitalize()}**" if plan.get('sector') else ""
    metric_type = plan.get('metric', 'mixed')

    if metric_type == 'operations':
        return (
            f"### Operational Analysis{sector_str}\n"
            f"- Total active work orders: **{s['work_orders_count']}**\n"
            f"- Data quality: **{s['work_order_quality']['missing_recognized_cells']}** missing cells across work order fields.\n\n"
            f"### Data Insights\n"
            f"- Work Orders tracked across key clients with operational milestones recorded."
        )
    elif metric_type == 'sector_performance':
        sector_items = ", ".join(f"**{k}**: {v} deals" for k, v in s['sector_breakdown'].most_common(5))
        return (
            f"### Sector Breakdown\n"
            f"{sector_items}\n\n"
            f"### Pipeline Highlights\n"
            f"- Total deals across sectors: **{s['deals_count']}**\n"
            f"- Total pipeline value: **₹{money(s['pipeline_value'])}**"
        )
    else:
        return (
            f"### Answer for '{query}'{sector_str}\n"
            f"- Total deals in scope: **{s['deals_count']}**\n"
            f"- Total pipeline value: **₹{money(s['pipeline_value'])}**\n"
            f"- Average deal value: **₹{money(s['average_deal_value'])}**\n"
            f"- Active work orders: **{s['work_orders_count']}**\n\n"
            f"### Key Insights\n"
            f"- Top sectors: {', '.join(f'{k} ({v})' for k,v in s['sector_breakdown'].most_common(4)) or 'N/A'}\n"
            f"- Top stages: {', '.join(f'{k} ({v})' for k,v in s['stage_breakdown'].most_common(4)) or 'N/A'}\n\n"
            f"### Data Quality Notice\n"
            f"- Deals missing cells: **{s['deal_quality']['missing_recognized_cells']}** | Work Orders missing cells: **{s['work_order_quality']['missing_recognized_cells']}**"
        )

def build_leadership_update(deals, work_orders, api_key, model):
    s = summarize(deals, work_orders, {})
    llm_payload = clean_summary_for_llm(s)
    prompt = f"""
Create a short leadership update using only these computed live Monday.com results:
{json.dumps(llm_payload, default=str, indent=2)}
Use sections: Pipeline, Operations, Risks/Data Quality, Suggested focus.
Do not invent facts.
"""
    raw = call_nvidia(prompt, api_key, model)
    if raw:
        return raw
    return (
        f"### Pipeline\n"
        f"- {s['deals_count']} deals; populated pipeline amount totals {money(s['pipeline_value'])}.\n"
        f"- Main sectors: {', '.join(f'{k} ({v})' for k,v in s['sector_breakdown'].most_common(5)) or 'not available'}.\n\n"
        f"### Operations\n"
        f"- {s['work_orders_count']} work orders returned.\n\n"
        f"### Risks / Data Quality\n"
        f"- Deals have {s['deal_quality']['missing_recognized_cells']} missing recognized-field cells.\n"
        f"- Work Orders have {s['work_order_quality']['missing_recognized_cells']} missing recognized-field cells.\n\n"
        f"### Suggested focus\n"
        f"- Validate missing commercial fields and review the largest pipeline stages before the next leadership update."
    )
