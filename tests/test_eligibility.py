import unittest
from uuid import UUID, uuid4
from tests import test_profiles as fixtures
from app.jobs.eligibility import compare
from app.jobs.extractions import router as extractions_router
from app.jobs.router import router as jobs_router
from app.profiles.schemas import Preferences

def prefs(*paths):
    return Preferences.model_validate({"pathways": list(paths)}).model_dump(mode="json")

def path(pid="p", **criteria):
    return {"id": pid, "label": pid, **criteria}

def choice(mode, *values):
    return {"mode": mode, "values": list(values)}

def claim(key, value=None, knowledge="explicit"):
    return {"id": uuid4(), "field_key": key, "knowledge": knowledge, "value": value}

def money(**values):
    return {"currency": "BRL", "currency_basis": "advertised", "period": "month", "amount_basis": "gross", **values}

def want(minimum="5000", **values):
    return {"mode": "required", "accepted_currencies": ["BRL"], "currency_basis": "advertised", "minimum": minimum,
            "period": "month", "amount_basis": "gross", **values}

def result(preferences, claims):
    return compare(preferences, claims).eligibility

def criterion(preferences, claims, key):
    return next(c for c in compare(preferences, claims).pathways[0].criteria if c.key == key)

class RulesTest(unittest.TestCase):
    def test_same_job_gives_different_results_for_different_profiles(self):
        job = [claim("work_arrangement", "remote"), claim("work_countries", {"countries": ["BR"]})]
        canada = prefs(path(work_countries=choice("required", "CA"), work_arrangements=choice("required", "remote")))
        brazil = prefs(path(work_countries=choice("required", "BR"), work_arrangements=choice("required", "remote")))
        self.assertEqual(result(canada, job), "incompatible")
        self.assertEqual(result(brazil, job), "compatible")

    def test_remote_is_never_treated_as_worldwide(self):
        profile = prefs(path(work_countries=choice("required", "CA")))
        self.assertEqual(result(profile, [claim("work_arrangement", "remote")]), "needs_confirmation")
        self.assertEqual(result(profile, [claim("work_countries", {"countries": ["US"]})]), "incompatible")

    def test_sponsorship(self):
        profile = prefs(path(sponsorship=choice("required", "offered")))
        self.assertEqual(result(profile, [claim("sponsorship", "not_offered")]), "incompatible")
        self.assertEqual(result(profile, []), "needs_confirmation")
        self.assertEqual(result(profile, [claim("sponsorship", "offered")]), "compatible")
        self.assertEqual(result(prefs(path(sponsorship=choice("required", "not_needed"))), [claim("sponsorship", "not_offered")]), "compatible")

    def test_employer_country_is_global_and_missing_evidence_is_not_compatible(self):
        profile = prefs(path("remote", work_arrangements=choice("required", "remote")),
                        path("office", work_arrangements=choice("required", "on_site")))
        profile["employer_countries"] = choice("required", "BR")
        job = [claim("work_arrangement", "remote"), claim("work_countries", {"countries": ["BR"]})]
        self.assertEqual(result(profile, job), "needs_confirmation")
        self.assertEqual(result(profile, job + [claim("employer_countries", {"countries": ["US"]})]), "incompatible")
        found = compare(profile, job + [claim("employer_countries", {"countries": ["BR"]})])
        self.assertEqual(found.eligibility, "compatible")
        self.assertTrue(all(any(c.key == "employer_countries" for c in p.criteria) for p in found.pathways))
        self.assertEqual(result(profile, job + [claim("employer_countries", {"countries": ["BR"]}, "inferred")]), "needs_confirmation")
        profile["employer_countries"] = choice("preferred", "BR")
        self.assertEqual(result(profile, job), "compatible")

    def test_authorization_declaration_requires_sponsorship_for_relevant_country(self):
        profile = prefs(path(work_countries=choice("required", "US"),
                             authorizations=[{"country": "US", "status": "requires_sponsorship"}]))
        job = [claim("work_countries", {"countries": ["US"]})]
        self.assertEqual(result(profile, job), "needs_confirmation")
        self.assertEqual(result(profile, job + [claim("sponsorship", "not_offered")]), "incompatible")
        self.assertEqual(result(profile, job + [claim("sponsorship", "offered")]), "compatible")
        self.assertEqual(result(profile, job + [claim("sponsorship", "offered", "inferred")]), "needs_confirmation")

    def test_authorization_country_options_and_pathway_scope(self):
        declarations = [{"country": "US", "status": "requires_sponsorship"}, {"country": "BR", "status": "authorized"}]
        profile = prefs(path(authorizations=declarations))
        job = [claim("work_countries", {"countries": ["BR", "US"]}), claim("sponsorship", "not_offered")]
        self.assertEqual(result(profile, job), "compatible")
        profile["pathways"][0]["work_countries"] = choice("required", "US")
        self.assertEqual(result(profile, job), "incompatible")
        profile["pathways"][0]["work_countries"] = choice("preferred", "US")
        self.assertEqual(result(profile, job), "compatible")
        profile["pathways"][0]["work_countries"] = choice("required", "BR")
        self.assertEqual(result(profile, job), "compatible")

    def test_unknown_or_missing_authorization_country_stays_unresolved(self):
        profile = prefs(path(authorizations=[{"country": "US", "status": "requires_sponsorship"}]))
        self.assertEqual(result(profile, [claim("sponsorship", "not_offered")]), "needs_confirmation")
        self.assertEqual(result(profile, [claim("work_countries", {"countries": ["CA"]})]), "needs_confirmation")
        profile["pathways"][0]["authorizations"][0]["status"] = "unknown"
        self.assertEqual(result(profile, [claim("work_countries", {"countries": ["US"]}),
                                          claim("sponsorship", "offered")]), "needs_confirmation")

    def test_authorization_conflict_with_not_needed_does_not_bypass_declaration(self):
        profile = prefs(path(sponsorship=choice("required", "not_needed"),
                             authorizations=[{"country": "US", "status": "requires_sponsorship"}]))
        job = [claim("work_countries", {"countries": ["US"]})]
        self.assertEqual(result(profile, job + [claim("sponsorship", "not_offered")]), "incompatible")
        self.assertEqual(result(profile, job + [claim("sponsorship", "offered")]), "needs_confirmation")

    def test_authorization_is_scoped_to_each_alternative_pathway(self):
        profile = prefs(path("us", work_countries=choice("required", "US"),
                             authorizations=[{"country": "US", "status": "requires_sponsorship"}]),
                        path("br", work_countries=choice("required", "BR"),
                             authorizations=[{"country": "BR", "status": "authorized"}]))
        found = compare(profile, [claim("work_countries", {"countries": ["BR", "US"]}), claim("sponsorship", "not_offered")])
        self.assertEqual(found.eligibility, "compatible")
        self.assertEqual([p.eligibility for p in found.pathways], ["incompatible", "compatible"])

    def test_explicit_contract_options_are_not_conflicting_claims(self):
        profile = prefs(path(contracts=choice("required", "employee")))
        options = claim("contract", {"alternatives": ["employee", "contractor"]})
        found = compare(profile, [options])
        self.assertEqual(found.eligibility, "compatible")
        self.assertEqual(found.pathways[0].criteria[0].claim_ids, [options["id"]])
        self.assertEqual(result(profile, [claim("contract", {"alternatives": ["contractor", "self_employed"]})]), "incompatible")
        self.assertEqual(result(profile, [claim("contract", options["value"], "inferred")]), "needs_confirmation")
        self.assertEqual(result(profile, [options, claim("contract", "self_employed")]), "needs_confirmation")

    def test_only_explicit_and_consistent_claims_prove_anything(self):
        profile = prefs(path(contracts=choice("required", "employee")))
        self.assertEqual(result(profile, [claim("contract", "employee", "inferred")]), "needs_confirmation")
        self.assertEqual(result(profile, [claim("contract", None, "not_provided")]), "needs_confirmation")
        self.assertEqual(result(profile, [claim("contract", "employee"), claim("contract", "contractor")]), "needs_confirmation")
        self.assertEqual(result(profile, [claim("contract", "employee")]), "compatible")
        self.assertEqual(result(profile, [claim("contract", "contractor")]), "incompatible")

    def test_compensation(self):
        profile = prefs(path(compensation=want()))
        check = lambda *claims: criterion(profile, list(claims), "compensation")
        self.assertEqual(check().result, "needs_confirmation")
        self.assertEqual(check(claim("compensation", money(minimum="8000", maximum="10000"))).result, "compatible")
        self.assertEqual(check(claim("compensation", money(maximum="4000"))).result, "incompatible")
        self.assertEqual(check(claim("compensation", money(minimum="3000"))).result, "needs_confirmation")
        self.assertEqual(check(claim("compensation", money(minimum="9000"))).result, "compatible")
        self.assertEqual(check(claim("compensation", money(maximum="90000", currency="USD", period="year"))).result, "incompatible")
        self.assertEqual(check(claim("compensation", money(maximum="9000", amount_basis="net"))).result, "needs_confirmation")
        self.assertEqual(check(claim("compensation", money(maximum="9000", currency_basis="actual_payment"))).result, "needs_confirmation")
        self.assertEqual(check(claim("compensation", money(maximum="9000")), claim("compensation", money(maximum="500"))).result, "needs_confirmation")

    def test_unknown_amount_basis_is_never_compared(self):
        profile = prefs(path(compensation=want(amount_basis="unknown")))
        self.assertEqual(criterion(profile, [claim("compensation", money(maximum="9000", amount_basis="unknown"))], "compensation").result, "needs_confirmation")

    def test_alternative_pathways(self):
        job = [claim("work_arrangement", "remote")]
        no = path("no", work_arrangements=choice("required", "on_site"))
        yes = path("yes", work_arrangements=choice("required", "remote"))
        ask = path("ask", contracts=choice("required", "employee"))
        self.assertEqual(result(prefs(no, yes), job), "compatible")
        self.assertEqual(result(prefs(no, no | {"id": "no2"}), job), "incompatible")
        self.assertEqual(result(prefs(no, ask), job), "needs_confirmation")

    def test_preferred_and_open_criteria_never_eliminate(self):
        job = [claim("work_arrangement", "remote")]
        profile = prefs(path(work_arrangements=choice("preferred", "on_site"), contracts=choice("unrestricted"),
                             sponsorship=choice("unspecified")))
        found = compare(profile, job)
        self.assertEqual(found.eligibility, "compatible")
        self.assertEqual(found.pathways[0].required_criteria, 0)
        self.assertEqual([(c.key, c.strength, c.result) for c in found.pathways[0].criteria], [("work_arrangement", "preferred", "incompatible")])

    def test_free_text_authorization_restriction_needs_review(self):
        profile = prefs(path(work_arrangements=choice("required", "remote")))
        found = compare(profile, [claim("work_arrangement", "remote"), claim("authorization_restriction", "Must hold US work authorization")])
        self.assertEqual(found.eligibility, "needs_confirmation")

    def test_profile_without_pathways_is_incomplete_and_fit_is_not_assessed(self):
        found = compare(prefs(), [claim("work_arrangement", "remote")])
        self.assertEqual((found.eligibility, found.pathways, found.technical_fit), ("incomplete_profile", [], "not_assessed"))
        self.assertEqual(found.rules_version, "rules-v2")

TEXT = "Remote role, Canada only. Sponsorship not offered."

def at(fragment):
    start = TEXT.index(fragment)
    return {"start_char": start, "end_char": start + len(fragment), "excerpt": fragment}

class ComparisonEndpointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ProfilesTest.setUpClass.__func__(cls)
        cls.app.include_router(jobs_router)
        cls.app.include_router(extractions_router)
    @classmethod
    def tearDownClass(cls):
        fixtures.ProfilesTest.tearDownClass.__func__(cls)
    def setUp(self):
        self.owner = self.client.post("/career/owners", json={"label": "Synthetic comparison owner"}).json()["id"]
        job = self.client.post(f"/career/owners/{self.owner}/jobs", json={"label": "Synthetic vacancy", "original_text": TEXT}).json()["id"]
        self.path = f"/career/owners/{self.owner}/jobs/{job}/snapshots/1/extractions"
        run = self.client.post(self.path, json={"extractor": "manual-v1", "claims": [
            {"field_key": "work_countries", "knowledge": "explicit", "value": {"countries": ["CA"]}, "evidence": [at("Canada only")]},
            {"field_key": "sponsorship", "knowledge": "explicit", "value": "not_offered", "evidence": [at("Sponsorship not offered")]}]})
        self.assertEqual(run.status_code, 201, run.text)
        self.run_id = run.json()["id"]
    def profile(self, country):
        data = {"label": "Synthetic", "preferences": {"pathways": [{"id": "p", "label": "P", "work_countries": {"mode": "required", "values": [country]}}]}}
        r = self.client.post(f"/career/owners/{self.owner}/profiles", json=data)
        return r.json()["id"]
    def compare(self, profile, version=1, owner=None):
        url = self.path.replace(self.owner, owner or self.owner) + f"/{self.run_id}/comparison"
        return self.client.get(url, params={"profile_id": profile, "profile_version": version})
    def test_same_extraction_different_profiles_and_nothing_is_saved(self):
        canada, brazil = self.profile("CA"), self.profile("BR")
        self.assertEqual(self.compare(canada).json()["eligibility"], "compatible")
        self.assertEqual(self.compare(brazil).json()["eligibility"], "incompatible")
        self.assertEqual(len(self.client.get(self.path).json()), 1)
    def test_not_found_cases_and_validation(self):
        profile = self.profile("CA")
        other = self.client.post("/career/owners", json={"label": "Other"}).json()["id"]
        self.assertEqual(self.compare(profile, owner=other).status_code, 404)
        self.assertEqual(self.compare(profile, version=9).status_code, 404)
        self.assertEqual(self.compare(str(uuid4())).status_code, 404)
        self.assertEqual(self.compare(profile, version=0).status_code, 422)
        self.assertEqual(self.client.get(f"{self.path}/{self.run_id}/comparison").status_code, 422)

if __name__ == "__main__":
    unittest.main()
