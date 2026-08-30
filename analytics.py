import json, re
from datetime import datetime, date
from collections import Counter, defaultdict

ALIASES = {
    "sector": ["sector", "industry", "vertical", "market"],
    "amount": ["amount", "deal value", "deal size", "value", "revenue", "price", "contract value"],
    "status": ["status", "stage", "deal stage", "pipeline stage"],
    "date": ["date", "close date", "expected close", "created", "start date", "end date"],
    "client": ["client", "customer", "account", "company", "organization"],
    "project": ["project", "work order", "workorder"],
}

def norm(s):
    if s is None or str(s).lower().strip() in ("none", "null", ""):
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

def parse_number(s):
    if s is None: return None
    s = str(s).replace(",", "").replace("₹", "").replace("$", "").replace("€", "").strip()
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None

def parse_date(s):
    if not s or str(s).lower().strip() in ("none", "null", ""): return None
    s = str(s).strip()
    candidates = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y"
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None

def column_map(board):
    result = {}
    for c in board["columns"]:
        n = norm(c["title"])
        for key, aliases in ALIASES.items():
            if any(a in n for a in aliases):
                result.setdefault(key, []).append(c["id"])
    return result

def rows(board):
    cmap = column_map(board)
    out = []
    missing_cells = 0
    for item in board["items"]:
        row = {"_id": item["id"], "_name": item["name"]}
        values = {cv["id"]: cv.get("text") or "" for cv in item.get("column_values", [])}
        for key, ids in cmap.items():
            val = next((values.get(cid, "") for cid in ids if values.get(cid, "")), "")
            row[key] = val
            if not val:
                missing_cells += 1
        row["_created_at"] = item.get("created_at")
        row["_updated_at"] = item.get("updated_at")
        out.append(row)
    return out, cmap, missing_cells

def quality_report(board):
    rs, cmap, missing = rows(board)
    return {
        "board": board["name"],
        "rows": len(rs),
        "recognized_fields": sorted(cmap.keys()),
        "unmapped_columns": [
            c["title"] for c in board["columns"]
            if not any(c["id"] in ids for ids in cmap.values())
        ],
        "missing_recognized_cells": missing,
    }

def filter_rows(rs, plan):
    sector = norm(plan.get("sector", ""))
    start = parse_date(plan.get("start_date"))
    end = parse_date(plan.get("end_date"))
    result = []
    for r in rs:
        if sector and sector not in norm(r.get("sector", "")):
            continue
        d = parse_date(r.get("date"))
        if start and (not d or d < start): continue
        if end and (not d or d > end): continue
        result.append(r)
    return result

def summarize(deals_board, work_orders_board, plan):
    deals, _, _ = rows(deals_board)
    wo, _, _ = rows(work_orders_board)
    deals = filter_rows(deals, plan)
    wo = filter_rows(wo, plan)

    amounts = [parse_number(r.get("amount")) for r in deals]
    amounts = [x for x in amounts if x is not None]
    pipeline = sum(amounts)
    sectors = Counter(r.get("sector") or "Unknown" for r in deals)
    statuses = Counter(r.get("status") or "Unknown" for r in deals)

    return {
        "deals_count": len(deals),
        "pipeline_value": pipeline,
        "average_deal_value": pipeline / len(amounts) if amounts else None,
        "sector_breakdown": sectors,
        "stage_breakdown": statuses,
        "work_orders_count": len(wo),
        "deal_quality": quality_report(deals_board),
        "work_order_quality": quality_report(work_orders_board),
        "sample_deals": deals[:10],
        "sample_work_orders": wo[:10],
    }
