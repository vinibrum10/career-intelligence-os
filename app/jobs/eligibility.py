"""Deterministic eligibility rules: saved profile preferences vs. explicit job claims. No AI, no conversions."""
import json
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel

RULES_VERSION = "rules-v1"
Result = Literal["compatible", "incompatible", "needs_confirmation"]
OK, NO, ASK = "compatible", "incompatible", "needs_confirmation"

class Criterion(BaseModel):
    key: str
    strength: Literal["required", "preferred"]
    result: Result
    explanation: str
    claim_ids: list[UUID] = []

class PathwayResult(BaseModel):
    id: str
    label: str
    eligibility: Result
    required_criteria: int  # 0 means "no configured restrictions", not proof of authorization
    criteria: list[Criterion]

class Comparison(BaseModel):
    rules_version: str = RULES_VERSION
    eligibility: Result | Literal["incomplete_profile"]
    technical_fit: Literal["not_assessed"] = "not_assessed"
    pathways: list[PathwayResult]

def fact(claims, key):
    """Only explicit, non-conflicting claims prove a fact; otherwise return the reason it is unresolved."""
    mine = [c for c in claims if c["field_key"] == key]
    proven = [c for c in mine if c["knowledge"] == "explicit"]
    if not proven:
        why = "only inferred" if any(c["knowledge"] == "inferred" for c in mine) else "not provided"
        return None, [c["id"] for c in mine], f"{key}: {why}"
    if len({json.dumps(c["value"], sort_keys=True) for c in proven}) > 1:
        return None, [c["id"] for c in proven], f"{key}: conflicting explicit claims"
    return proven[0]["value"], [proven[0]["id"]], None

def worst(parts):
    results = [result for result, _ in parts]
    result = NO if NO in results else ASK if ASK in results else OK
    return result, "; ".join(text for _, text in parts)

def accepted(key, allowed, claims, pick=lambda value: value):
    value, ids, why = fact(claims, key)
    if why:
        return ASK, why, ids
    found = pick(value)
    ok = bool(set(found if isinstance(found, list) else [found]) & set(allowed))
    return (OK if ok else NO), f"{key} {found} {'matches' if ok else 'does not match'} accepted {sorted(allowed)}", ids

def sponsorship(choice, claims):
    if "not_needed" in choice["values"]:
        return OK, "sponsorship not needed", []
    value, ids, why = fact(claims, "sponsorship")
    if why:
        return ASK, why, ids
    return (OK, "sponsorship offered", ids) if value == "offered" else (NO, "sponsorship explicitly not offered", ids)

def compensation(pref, claims):
    value, ids, why = fact(claims, "compensation")
    if why:
        return ASK, why, ids
    parts = []
    same_basis = value["currency_basis"] == pref["currency_basis"]
    if pref["accepted_currencies"]:
        if not same_basis:
            parts.append((ASK, "advertised and actual payment currency differ"))
        else:
            ok = value["currency"] in pref["accepted_currencies"]
            parts.append((OK if ok else NO, f"currency {value['currency']} {'accepted' if ok else 'not accepted'}"))
    if pref["minimum"] is not None:
        comparable = (same_basis and value["currency"] == pref["accepted_currencies"][0] and value["period"] == pref["period"]
                      and value["amount_basis"] == pref["amount_basis"] != "unknown")
        if not comparable:
            parts.append((ASK, "currency, period or gross/net basis not comparable; no conversion applied"))
        else:
            need = Decimal(pref["minimum"])
            if value.get("maximum") is not None:
                ok = Decimal(value["maximum"]) >= need
                parts.append((OK if ok else NO, f"advertised maximum {'reaches' if ok else 'is below'} required minimum"))
            else:
                ok = Decimal(value["minimum"]) >= need
                parts.append((OK, "advertised minimum meets required minimum") if ok else (ASK, "only a lower minimum is advertised"))
    return (*worst(parts), ids)

def criteria(path, claims):
    checks = [
        ("work_arrangement", path["work_arrangements"], lambda c: accepted("work_arrangement", c["values"], claims)),
        ("work_countries", path["work_countries"], lambda c: accepted("work_countries", c["values"], claims, lambda v: v["countries"])),
        ("sponsorship", path["sponsorship"], lambda c: sponsorship(c, claims)),
        ("contract", path["contracts"], lambda c: accepted("contract", c["values"], claims)),
        ("compensation", path["compensation"], lambda c: compensation(c, claims)),
    ]
    out = []
    for key, choice, evaluate in checks:
        if choice["mode"] in ("required", "preferred"):
            result, text, ids = evaluate(choice)
            out.append(Criterion(key=key, strength=choice["mode"], result=result, explanation=text, claim_ids=ids))
    restriction = [c["id"] for c in claims if c["field_key"] == "authorization_restriction" and c["knowledge"] == "explicit"]
    if restriction:
        out.append(Criterion(key="authorization_restriction", strength="required", result=ASK, claim_ids=restriction,
                             explanation="free-text restriction cannot be decided by rules; review it"))
    return out

def compare(preferences, claims):
    """preferences: stored profile JSON; claims: dicts with id, field_key, knowledge, value."""
    pathways = []
    for path in preferences["pathways"]:
        items = criteria(path, claims)
        required = [item.result for item in items if item.strength == "required"]
        result = NO if NO in required else ASK if ASK in required else OK
        pathways.append(PathwayResult(id=path["id"], label=path["label"], eligibility=result,
                                      required_criteria=len(required), criteria=items))
    if not pathways:
        return Comparison(eligibility="incomplete_profile", pathways=[])
    results = [p.eligibility for p in pathways]
    overall = OK if OK in results else NO if all(r == NO for r in results) else ASK
    return Comparison(eligibility=overall, pathways=pathways)
