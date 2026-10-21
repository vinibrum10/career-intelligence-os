"""Deterministic eligibility rules: saved profile preferences vs. explicit job claims. No AI, no conversions."""
import json
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel

RULES_VERSION = "rules-v2"
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

def authorization(path, claims):
    """Evaluate self-declarations only for countries supported by this job and pathway.

    Several permitted countries are alternatives. This is not legal verification.
    """
    countries, ids, why = fact(claims, "work_countries")
    if why:
        return ASK, f"cannot select an authorization declaration: {why}", ids
    eligible = set(countries["countries"])
    if path["work_countries"]["mode"] == "required":
        eligible &= set(path["work_countries"]["values"])
    if not eligible:
        return ASK, "no matching work country for an authorization declaration", ids
    declarations = {entry["country"]: entry["status"] for entry in path["authorizations"]}
    outcomes, reasons = [], []
    for country in sorted(eligible):
        status = declarations.get(country, "unknown")
        if status == "authorized":
            outcome, reason = OK, "authorized according to the user's declaration"
        elif status == "requires_sponsorship":
            outcome, reason, sponsor_ids = sponsorship({"values": ["offered"]}, claims)
            ids = list(dict.fromkeys([*ids, *sponsor_ids]))
            choice = path["sponsorship"]
            if outcome == OK and choice["mode"] in ("required", "preferred") and choice["values"] == ["not_needed"]:
                outcome, reason = ASK, "profile declares both sponsorship required and not needed; review the profile"
        else:
            outcome, reason = ASK, "authorization declaration is missing or unknown"
        outcomes.append(outcome)
        reasons.append(f"{country}: {reason}")
    overall = OK if OK in outcomes else NO if all(r == NO for r in outcomes) else ASK
    return overall, "; ".join(reasons), ids

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
        ("contract", path["contracts"], lambda c: accepted("contract", c["values"], claims,
            lambda v: v["alternatives"] if isinstance(v, dict) else v)),
        ("compensation", path["compensation"], lambda c: compensation(c, claims)),
    ]
    out = []
    for key, choice, evaluate in checks:
        if choice["mode"] in ("required", "preferred"):
            result, text, ids = evaluate(choice)
            out.append(Criterion(key=key, strength=choice["mode"], result=result, explanation=text, claim_ids=ids))
    if path["authorizations"]:
        result, text, ids = authorization(path, claims)
        out.append(Criterion(key="authorization", strength="required", result=result, explanation=text, claim_ids=ids))
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
        employer = preferences["employer_countries"]
        if employer["mode"] in ("required", "preferred"):
            result, text, ids = accepted("employer_countries", employer["values"], claims, lambda v: v["countries"])
            items.append(Criterion(key="employer_countries", strength=employer["mode"], result=result,
                                   explanation=text, claim_ids=ids))
        required = [item.result for item in items if item.strength == "required"]
        result = NO if NO in required else ASK if ASK in required else OK
        pathways.append(PathwayResult(id=path["id"], label=path["label"], eligibility=result,
                                      required_criteria=len(required), criteria=items))
    if not pathways:
        return Comparison(eligibility="incomplete_profile", pathways=[])
    results = [p.eligibility for p in pathways]
    overall = OK if OK in results else NO if all(r == NO for r in results) else ASK
    return Comparison(eligibility=overall, pathways=pathways)
