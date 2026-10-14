import unittest
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from tests import test_profiles as fixtures
from app.jobs.extractions import router as extractions_router
from app.jobs.models import ClaimEvidence, ExtractionRun, JobClaim
from app.jobs.router import router as jobs_router

TEXT = "Analista de Dados — remoto\r\nSalário: R$ 8.000 a R$ 10.000 (CLT)\nSalary up to USD 90k.\nExperiência: TARA, PSS/E ou similar.\n"

def at(fragment, nth=0):
    start = -1
    for _ in range(nth + 1):
        start = TEXT.index(fragment, start + 1)
    return {"start_char": start, "end_char": start + len(fragment), "excerpt": fragment}

def comp(fragment, **values):
    base = {"currency": "BRL", "currency_basis": "advertised", "period": "month", "amount_basis": "unknown"}
    return {"field_key": "compensation", "knowledge": "explicit", "requirement": "informational",
            "value": {**base, **values}, "evidence": [at(fragment)]}

class ExtractionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ProfilesTest.setUpClass.__func__(cls)
        cls.app.include_router(jobs_router)
        cls.app.include_router(extractions_router)
    @classmethod
    def tearDownClass(cls):
        fixtures.ProfilesTest.tearDownClass.__func__(cls)
    def setUp(self):
        r = self.client.post("/career/owners", json={"label": "Synthetic extraction owner"})
        self.owner = r.json()["id"]
        r = self.client.post(f"/career/owners/{self.owner}/jobs", json={"label": "Synthetic vacancy", "original_text": TEXT})
        self.assertEqual(r.status_code, 201, r.text)
        self.job = r.json()["id"]
        self.path = f"/career/owners/{self.owner}/jobs/{self.job}/snapshots/1/extractions"
    def post(self, claims, path=None):
        return self.client.post(path or self.path, json={"extractor": "manual-v1", "claims": claims})
    def count(self):
        return len(self.client.get(self.path).json())

    def test_claims_keep_exact_evidence_and_normalized_values(self):
        r = self.post([
            {"field_key": "work_arrangement", "knowledge": "explicit", "requirement": "required", "value": "remote", "evidence": [at("remoto")]},
            {"field_key": "contract", "knowledge": "explicit", "value": "employee", "evidence": [at("CLT")]},
            {"field_key": "sponsorship", "knowledge": "not_provided"},
            {"field_key": "working_time", "knowledge": "inferred", "value": "full_time", "basis": "CLT vacancies are usually full time"},
        ])
        self.assertEqual(r.status_code, 201, r.text)
        body = r.json()
        self.assertEqual([c["field_key"] for c in body["claims"]], ["work_arrangement", "contract", "sponsorship", "working_time"])
        first = body["claims"][0]
        self.assertEqual(first["evidence"][0]["excerpt"], "remoto")
        self.assertEqual(TEXT[first["evidence"][0]["start_char"]:first["evidence"][0]["end_char"]], "remoto")
        self.assertIsNone(body["claims"][2]["value"])
        self.assertEqual(self.client.get(f"{self.path}/{body['id']}").json(), body)
        self.assertEqual(self.client.get(self.path).json(), [body])

    def test_evidence_after_crlf_and_unicode_matches_by_character(self):
        fragment = "Salary up to USD 90k."
        r = self.post([comp(fragment, maximum="90000", currency="USD", period="year", amount_basis="gross")])
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["claims"][0]["value"]["maximum"], "90000")

    def test_conflicting_salaries_are_both_preserved(self):
        r = self.post([comp("R$ 8.000 a R$ 10.000", minimum="8000", maximum="10000"),
                       comp("Salary up to USD 90k.", maximum="90000", currency="USD", period="year")])
        self.assertEqual(r.status_code, 201, r.text)
        currencies = [c["value"]["currency"] for c in r.json()["claims"]]
        self.assertEqual(currencies, ["BRL", "USD"])

    def test_skill_alternatives_stay_one_requirement(self):
        group = {"field_key": "skill_group", "knowledge": "explicit", "requirement": "required",
                 "value": {"alternatives": ["TARA", "PSS/E", "similar"]}, "evidence": [at("TARA, PSS/E ou similar")]}
        r = self.post([group])
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(len(r.json()["claims"]), 1)
        self.assertEqual(r.json()["claims"][0]["value"]["alternatives"], ["TARA", "PSS/E", "similar"])

    def test_invalid_claims_are_rejected_and_nothing_is_saved(self):
        good = {"field_key": "work_arrangement", "knowledge": "explicit", "value": "remote", "evidence": [at("remoto")]}
        bad = [
            {**good, "evidence": []},
            {**good, "evidence": [{**at("remoto"), "excerpt": "remote"}]},
            {**good, "evidence": [{"start_char": 0, "end_char": len(TEXT) + 5, "excerpt": TEXT + "extra"}]},
            {**good, "value": "anywhere"},
            {**good, "field_key": "career_role"},
            {**good, "salary": 1},
            {"field_key": "working_time", "knowledge": "inferred", "value": "full_time"},
            {"field_key": "sponsorship", "knowledge": "not_provided", "value": "offered"},
            {"field_key": "sponsorship", "knowledge": "explicit", "evidence": [at("CLT")]},
            {"field_key": "work_countries", "knowledge": "explicit", "value": {"countries": ["br"]}, "evidence": [at("CLT")]},
            {"field_key": "work_countries", "knowledge": "explicit", "value": {"countries": ["BR", "BR"]}, "evidence": [at("CLT")]},
            comp("CLT", minimum="10", maximum="5"),
            comp("CLT"),
            {**comp("CLT", minimum="1"), "value": {"minimum": "1", "currency": "BRL"}},
        ]
        for claim in bad:
            with self.subTest(claim=claim):
                self.assertEqual(self.post([claim]).status_code, 422)
        self.assertEqual(self.post([]).status_code, 422)
        self.assertEqual(self.post([good, bad[1]]).status_code, 422)
        self.assertEqual(self.count(), 0)

    def test_new_run_does_not_change_previous_run(self):
        first = self.post([{"field_key": "contract", "knowledge": "explicit", "value": "employee", "evidence": [at("CLT")]}]).json()
        second = self.post([{"field_key": "contract", "knowledge": "explicit", "value": "contractor", "evidence": [at("CLT")]}]).json()
        self.assertEqual(self.client.get(f"{self.path}/{first['id']}").json()["claims"][0]["value"], "employee")
        self.assertEqual({r["id"] for r in self.client.get(self.path).json()}, {first["id"], second["id"]})
        for method in (self.client.put, self.client.patch, self.client.delete):
            self.assertEqual(method(f"{self.path}/{first['id']}").status_code, 405)

    def test_owner_isolation_and_missing_parents(self):
        run = self.post([{"field_key": "contract", "knowledge": "explicit", "value": "employee", "evidence": [at("CLT")]}]).json()
        other = self.client.post("/career/owners", json={"label": "Other"}).json()["id"]
        foreign = f"/career/owners/{other}/jobs/{self.job}/snapshots/1/extractions"
        self.assertEqual(self.client.get(foreign).status_code, 404)
        self.assertEqual(self.client.get(f"{foreign}/{run['id']}").status_code, 404)
        self.assertEqual(self.post([{"field_key": "contract", "knowledge": "not_provided"}], foreign).status_code, 404)
        self.assertEqual(self.client.get(self.path.replace("/snapshots/1/", "/snapshots/9/")).status_code, 404)
        self.assertEqual(self.client.get(f"{self.path}/{UUID(int=1)}").status_code, 404)

    def test_database_rejects_cross_owner_and_inconsistent_rows(self):
        run = self.post([{"field_key": "contract", "knowledge": "explicit", "value": "employee", "evidence": [at("CLT")]}]).json()
        other = UUID(self.client.post("/career/owners", json={"label": "Other"}).json()["id"])
        run_id = UUID(run["id"]); claim_id = UUID(run["claims"][0]["id"]); owner = UUID(self.owner)
        rows = [
            JobClaim(owner_id=other, run_id=run_id, position=9, field_key="contract", knowledge="not_provided"),
            ClaimEvidence(owner_id=other, claim_id=claim_id, start_char=0, end_char=1, excerpt="x"),
            JobClaim(owner_id=owner, run_id=run_id, position=9, field_key="contract", knowledge="not_provided", value="employee"),
            JobClaim(owner_id=owner, run_id=run_id, position=9, field_key="contract", knowledge="explicit"),
            JobClaim(owner_id=owner, run_id=run_id, position=9, field_key="contract", knowledge="inferred", value="employee"),
            JobClaim(owner_id=owner, run_id=run_id, position=9, field_key="contract", knowledge="guess", value="employee"),
            ClaimEvidence(owner_id=owner, claim_id=claim_id, start_char=5, end_char=5, excerpt="x"),
            ExtractionRun(owner_id=other, snapshot_id=UUID(self.client.get(f"/career/owners/{self.owner}/jobs/{self.job}/snapshots/1").json()["id"]), extractor="x"),
        ]
        for row in rows:
            with self.subTest(row=type(row).__name__), self.sessions() as session:
                session.add(row)
                with self.assertRaises(IntegrityError):
                    session.commit()
                session.rollback()

if __name__ == "__main__":
    unittest.main()
