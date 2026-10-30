"""Deterministic eligibility rules: saved profile preferences vs. explicit job claims. No AI, no conversions."""
import json
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel

RULES_VERSION = "rules-v2"
Result = Literal["compatible", "incompatible", "needs_confirmation"]
OK, NO, ASK = "compatible", "incompatible", "needs_confirmation"

FIELD_LABELS = {
    "work_arrangement": "Modalidade", "work_countries": "Países de trabalho",
    "employer_countries": "País da empresa", "contract": "Contratação",
    "sponsorship": "Patrocínio", "compensation": "Remuneração",
}
VALUE_LABELS = {
    "remote": "remoto", "hybrid": "híbrido", "on_site": "presencial",
    "employee": "vínculo empregatício", "contractor": "prestação de serviço",
    "self_employed": "trabalho autônomo", "other": "outro vínculo",
}


def describe(value):
    if isinstance(value, list):
        return ", ".join(describe(item) for item in value)
    return VALUE_LABELS.get(value, str(value))

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
        why = ("há apenas uma inferência, sem informação explícita que confirme este dado"
               if any(c["knowledge"] == "inferred" for c in mine)
               else "este dado não foi informado nos fatos da vaga")
        return None, [c["id"] for c in mine], f"{FIELD_LABELS[key]}: {why}. É preciso confirmar."
    if len({json.dumps(c["value"], sort_keys=True) for c in proven}) > 1:
        return None, [c["id"] for c in proven], f"{FIELD_LABELS[key]}: há informações explícitas conflitantes na vaga. É preciso confirmar qual está correta."
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
    conclusion = "Há uma opção em comum." if ok else "As opções não coincidem."
    explanation = (f"{FIELD_LABELS[key]}: a vaga informa {describe(found)}; "
                   f"seu perfil aceita {describe(sorted(allowed))}. {conclusion}")
    return (OK if ok else NO), explanation, ids

def sponsorship(choice, claims):
    if "not_needed" in choice["values"]:
        return OK, "Seu perfil declara que não precisa de patrocínio.", []
    value, ids, why = fact(claims, "sponsorship")
    if why:
        return ASK, why, ids
    return (OK, "A vaga informa que oferece o patrocínio indicado no perfil.", ids) if value == "offered" else (NO, "O perfil indica patrocínio, mas a vaga informa que não o oferece.", ids)

def authorization(path, claims):
    """Evaluate self-declarations only for countries supported by this job and pathway.

    Several permitted countries are alternatives. This is not legal verification.
    """
    countries, ids, why = fact(claims, "work_countries")
    if why:
        return ASK, f"Não foi possível escolher a declaração de autorização aplicável. {why}", ids
    eligible = set(countries["countries"])
    if path["work_countries"]["mode"] == "required":
        eligible &= set(path["work_countries"]["values"])
    if not eligible:
        return ASK, "Não há país em comum entre a vaga e este caminho para avaliar a declaração de autorização.", ids
    declarations = {entry["country"]: entry["status"] for entry in path["authorizations"]}
    outcomes, reasons = [], []
    for country in sorted(eligible):
        status = declarations.get(country, "unknown")
        if status == "authorized":
            outcome, reason = OK, "Você declarou ter autorização para trabalhar neste país; essa declaração não foi verificada."
        elif status == "requires_sponsorship":
            outcome, reason, sponsor_ids = sponsorship({"values": ["offered"]}, claims)
            ids = list(dict.fromkeys([*ids, *sponsor_ids]))
            choice = path["sponsorship"]
            if outcome == OK and choice["mode"] in ("required", "preferred") and choice["values"] == ["not_needed"]:
                outcome, reason = ASK, "O perfil declara precisar de patrocínio e também não precisar dele. Revise essas informações."
        else:
            outcome, reason = ASK, "A autorização para trabalhar neste país não foi informada ou está marcada como desconhecida."
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
            parts.append((ASK, "A vaga e o perfil usam bases diferentes para a moeda: valor anunciado ou pagamento efetivo. É preciso confirmar."))
        else:
            ok = value["currency"] in pref["accepted_currencies"]
            parts.append((OK if ok else NO, f"A moeda {value['currency']} {'é aceita' if ok else 'não é aceita'} pelo perfil."))
    if pref["minimum"] is not None:
        comparable = (same_basis and value["currency"] == pref["accepted_currencies"][0] and value["period"] == pref["period"]
                      and value["amount_basis"] == pref["amount_basis"] != "unknown")
        if not comparable:
            parts.append((ASK, "Não é possível comparar os valores: confira moeda, período e se são brutos ou líquidos. Nenhuma conversão foi aplicada."))
        else:
            need = Decimal(pref["minimum"])
            if value.get("maximum") is not None:
                ok = Decimal(value["maximum"]) >= need
                parts.append((OK if ok else NO, f"O valor máximo anunciado {'atinge o' if ok else 'fica abaixo do'} mínimo indicado no perfil."))
            else:
                ok = Decimal(value["minimum"]) >= need
                parts.append((OK, "O valor mínimo anunciado atende ao mínimo indicado no perfil.") if ok else (ASK, "A vaga informa apenas um mínimo abaixo do indicado no perfil. Falta confirmar se pode pagar o valor desejado."))
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
                             explanation="A vaga contém uma restrição de autorização em texto livre. Confira o trecho: as regras atuais não conseguem decidir esse caso."))
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
