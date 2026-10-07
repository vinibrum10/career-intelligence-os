"""API tests: SQLite locally; PostgreSQL in an explicitly isolated test database."""
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

TEST_URL = os.environ.get("PROFILE_TEST_DATABASE_URL")
os.environ.setdefault("DATABASE_URL", TEST_URL or "postgresql+psycopg://unused:unused@localhost/unused")

from app.database import get_session
from app.profiles.models import Base, Owner, Profile, ProfileVersion
from app.profiles.router import router


def sample():
    # Synthetic Canadian resident, unrelated to the founder's personal profile.
    return {"label": "Synthetic profile", "preferences": {
        "current_location": {"country": "CA", "region": "Ontario", "city": "Ottawa"},
        "pathways": [{"id": "remote", "label": "Remote from current country",
            "work_countries": {"mode": "required", "values": ["CA"]},
            "work_arrangements": {"mode": "required", "values": ["remote"]}},
            {"id": "relocate", "label": "Sponsored relocation",
             "work_countries": {"mode": "required", "values": ["DE"]},
             "relocation_allowed": True,
             "sponsorship": {"mode": "required", "values": ["offered"]}}],
    }}


class ProfilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if TEST_URL:
            url = make_url(TEST_URL)
            if url.get_backend_name() != "postgresql" or not (url.database or "").startswith("career_profile_test_"):
                raise RuntimeError("Tests require a dedicated career_profile_test_* PostgreSQL database")
            cls.engine = create_engine(TEST_URL)
        else:
            from sqlalchemy.dialects.postgresql import JSONB
            from sqlalchemy.ext.compiler import compiles

            @compiles(JSONB, "sqlite")
            def sqlite_jsonb(type_, compiler, **kwargs):
                return "JSON"

            cls.temp = TemporaryDirectory()
            database_path = str(Path(cls.temp.name) / "career.sqlite")
            cls.engine = create_engine("sqlite://", connect_args={"check_same_thread": False})

            @event.listens_for(cls.engine, "connect")
            def attach(dbapi, _):
                dbapi.execute("PRAGMA foreign_keys=ON")
                dbapi.execute("ATTACH DATABASE ? AS career", (database_path,))

            Base.metadata.create_all(cls.engine)
        cls.sessions = sessionmaker(cls.engine, expire_on_commit=False)
        cls.app = FastAPI()
        cls.app.include_router(router)

        def session_override():
            with cls.sessions() as session:
                yield session

        cls.app.dependency_overrides[get_session] = session_override
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.engine.dispose()
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def owner(self):
        response = self.client.post("/career/owners", json={"label": "Synthetic test owner"})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def create(self, owner_id, data=None):
        response = self.client.post(f"/career/owners/{owner_id}/profiles", json=data or sample())
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_update_preserves_history_and_rejects_stale_edits(self):
        owner = self.owner()
        created = self.create(owner)
        path = f"/career/owners/{owner}/profiles/{created['id']}"
        update = sample()
        update["expected_version"] = 1
        update["preferences"]["current_location"]["country"] = "AU"
        response = self.client.put(path, json=update)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["latest"]["version"], 2)
        self.assertEqual(self.client.put(path, json=update).status_code, 409)
        versions = self.client.get(path + "/versions").json()
        self.assertEqual([v["version"] for v in versions], [2, 1])
        self.assertEqual(versions[1]["preferences"]["current_location"]["country"], "CA")
        self.assertEqual(versions[0]["preferences"]["current_location"]["country"], "AU")

    def test_isolation_for_read_update_history_and_list(self):
        owner_a, owner_b = self.owner(), self.owner()
        profile = self.create(owner_a)
        wrong = f"/career/owners/{owner_b}/profiles/{profile['id']}"
        self.assertEqual(self.client.get(wrong).status_code, 404)
        self.assertEqual(self.client.get(wrong + "/versions").status_code, 404)
        self.assertEqual(self.client.put(wrong, json={**sample(), "expected_version": 1}).status_code, 404)
        self.assertEqual(self.client.get(f"/career/owners/{owner_b}/profiles").json(), [])

    def test_database_rejects_cross_owner_version(self):
        from uuid import UUID
        owner_a, owner_b = self.owner(), self.owner()
        profile = self.create(owner_a)
        with self.sessions() as session:
            session.add(ProfileVersion(owner_id=UUID(owner_b), profile_id=UUID(profile["id"]),
                version=2, preferences_json={}))
            with self.assertRaises(IntegrityError):
                session.commit()
            session.rollback()

    def test_profiles_can_have_different_preferences(self):
        owner = self.owner()
        first = self.create(owner)
        alternative = sample()
        alternative["preferences"]["pathways"][0]["work_arrangements"]["values"] = ["hybrid", "on_site"]
        second = self.create(owner, alternative)
        self.assertNotEqual(first["latest"]["preferences"], second["latest"]["preferences"])

    def test_unknown_unrestricted_and_negative_remain_distinct(self):
        data = sample()
        path = data["preferences"]["pathways"][0]
        path["contracts"] = {"mode": "unrestricted", "values": []}
        path["travel_allowed"] = False
        created = self.create(self.owner(), data)
        saved = created["latest"]["preferences"]["pathways"][0]
        self.assertEqual(saved["contracts"]["mode"], "unrestricted")
        self.assertEqual(saved["compensation"]["mode"], "unspecified")
        self.assertIs(saved["travel_allowed"], False)
        self.assertIsNone(saved["relocation_allowed"])

    def test_invalid_inputs_are_rejected_without_creating_profiles(self):
        owner = self.owner()
        url = f"/career/owners/{owner}/profiles"
        invalid = []
        item = sample(); item["preferences"]["current_location"]["country"] = "canada"; invalid.append(item)
        item = sample(); item["preferences"]["pathways"][0]["work_countries"]["values"] = []; invalid.append(item)
        item = sample(); item["preferences"]["pathways"][1]["id"] = "remote"; invalid.append(item)
        item = sample(); item["preferences"]["pathways"][0]["travel_allowed"] = "maybe"; invalid.append(item)
        item = sample(); item["preferences"]["unknown_setting"] = "ignored?"; invalid.append(item)
        item = sample(); item["preferences"]["pathways"][0]["compensation"] = {"mode": "required", "minimum": 10}; invalid.append(item)
        for value in invalid:
            with self.subTest(value=value):
                self.assertEqual(self.client.post(url, json=value).status_code, 422)
        self.assertEqual(self.client.get(url).json(), [])

    def test_explicit_currency_basis_and_decimal_roundtrip(self):
        data = sample()
        data["preferences"]["pathways"][0]["compensation"] = {
            "mode": "required", "accepted_currencies": ["CAD"], "currency_basis": "actual_payment",
            "minimum": "1234.56", "period": "month", "amount_basis": "gross",
        }
        created = self.create(self.owner(), data)
        saved = created["latest"]["preferences"]["pathways"][0]["compensation"]
        self.assertEqual(saved["minimum"], "1234.56")
        self.assertEqual(saved["currency_basis"], "actual_payment")

    def test_incomplete_profile_stays_unknown_without_career_default(self):
        created = self.create(self.owner(), {"label": "Incomplete", "preferences": {}})
        saved = created["latest"]["preferences"]
        self.assertEqual(saved["pathways"], [])
        self.assertIsNone(saved["current_location"]["country"])
        self.assertEqual(saved["career_roles"], {"mode": "unspecified", "values": []})

    def test_pagination_and_unknown_owner(self):
        owner = self.owner()
        self.create(owner); self.create(owner)
        self.assertEqual(len(self.client.get(f"/career/owners/{owner}/profiles?limit=1&offset=1").json()), 1)
        self.assertEqual(self.client.get(f"/career/owners/{owner}/profiles?limit=101").status_code, 422)
        self.assertEqual(self.client.get(f"/career/owners/{uuid4()}/profiles").status_code, 404)

    @unittest.skipUnless(TEST_URL, "PostgreSQL required to verify row-lock concurrency")
    def test_concurrent_edits_have_one_winner(self):
        owner = self.owner()
        profile = self.create(owner)
        path = f"/career/owners/{owner}/profiles/{profile['id']}"
        update = {**sample(), "expected_version": 1}
        def edit(_):
            with TestClient(self.app) as client:
                return client.put(path, json=deepcopy(update)).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(edit, range(2)))
        self.assertEqual(sorted(statuses), [200, 409])
        self.assertEqual(len(self.client.get(path + "/versions").json()), 2)


if __name__ == "__main__":
    unittest.main()
