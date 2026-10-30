import unittest
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from uuid import uuid4, UUID
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from tests import test_profiles as fixtures
from app.jobs.models import JobSnapshot
from app.jobs.router import router
from app.web import router as web_router
RAW = "  Synthetic vacancy\r\nAnalyst — energia ⚡\nRemoto? Não informado.\n  "
def sample():
    return {"label":"Synthetic vacancy", "original_text":RAW, "source_url":"https://example.com/jobs/42", "association_confirmed":True}
class JobsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.ProfilesTest.setUpClass.__func__(cls)
        cls.app.include_router(router)
        cls.app.include_router(web_router)
    @classmethod
    def tearDownClass(cls):
        fixtures.ProfilesTest.tearDownClass.__func__(cls)
    def owner(self):
        r=self.client.post("/career/owners",json={"label":"Synthetic job owner"})
        self.assertEqual(r.status_code,201,r.text)
        return r.json()["id"]
    def create(self,owner,data=None):
        r=self.client.post(f"/career/owners/{owner}/jobs",json=data or sample())
        self.assertEqual(r.status_code,201,r.text)
        return r.json()
    def test_screen_assets_and_profile_navigation(self):
        page=self.client.get("/jobs")
        self.assertEqual(page.status_code,200)
        self.assertEqual(page.headers["cache-control"],"no-store")
        self.assertIn("/jobs/assets/jobs.js",page.text)
        self.assertEqual(self.client.get("/jobs/assets/jobs.js").status_code,200)
        self.assertIn('href="/jobs"',self.client.get("/profiles").text)
    def test_exact_text_hash_and_unknown_time(self):
        owner=self.owner(); job=self.create(owner)
        result=self.client.get(f"/career/owners/{owner}/jobs/{job['id']}").json()["latest"]
        self.assertEqual(result["original_text"],RAW)
        self.assertEqual(result["content_sha256"],sha256(RAW.encode("utf-8")).hexdigest())
        self.assertIsNone(result["captured_at"])
        self.assertTrue(result["imported_at"])
        self.assertNotIn("original_text",self.client.get(f"/career/owners/{owner}/jobs").json()[0]["latest"])
    def test_history_and_stale_edit(self):
        owner=self.owner(); job=self.create(owner); path=f"/career/owners/{owner}/jobs/{job['id']}"
        data={**sample(),"original_text":"Different evidence","source_url":None,"association_confirmed":False,
              "expected_version":1,"captured_at":"2025-01-02T03:04:05+02:00"}
        r=self.client.post(path+"/snapshots",json=data)
        self.assertEqual(r.status_code,201,r.text)
        self.assertEqual(r.json()["latest"]["version"],2)
        old=self.client.get(path+"/snapshots/1").json()
        self.assertEqual(old["original_text"],RAW)
        self.assertEqual(old["source_url"],sample()["source_url"])
        self.assertTrue(old["association_confirmed"])
        self.assertEqual(self.client.post(path+"/snapshots",json=data).status_code,409)
        self.assertEqual([v["version"] for v in self.client.get(path+"/snapshots").json()],[2,1])
        self.assertEqual(self.client.get(path+"/snapshots/99").status_code,404)
    def test_owner_scoping_and_foreign_key(self):
        owner=self.owner(); other=self.owner(); job=self.create(owner); path=f"/career/owners/{other}/jobs/{job['id']}"
        self.assertEqual(self.client.get(path).status_code,404)
        self.assertEqual(self.client.get(path+"/snapshots/1").status_code,404)
        self.assertEqual(self.client.post(path+"/snapshots",json={**sample(),"expected_version":1}).status_code,404)
        self.assertEqual(self.client.get(f"/career/owners/{other}/jobs").json(),[])
        with self.sessions() as s:
            s.add(JobSnapshot(owner_id=UUID(other),source_id=UUID(job["id"]),version=2,label="Wrong owner",original_text="x",content_sha256="0"*64,association_confirmed=False))
            with self.assertRaises(IntegrityError): s.commit()
            s.rollback()
    def test_validation_no_records_created(self):
        owner=self.owner(); path=f"/career/owners/{owner}/jobs"
        invalid=[{"original_text":" "},{"original_text":"x\x00y"},{"original_text":"x"*100001},{"label":" "},
            {"source_url":"javascript:alert(1)"},{"source_url":"https://user:secret@example.com/"},{"source_url":None},
            {"captured_at":"2025-01-01T12:00:00"},{"salary":123}]
        for changes in invalid:
            with self.subTest(fields=list(changes)):
                self.assertEqual(self.client.post(path,json={**sample(),**changes}).status_code,422)
        self.assertEqual(self.client.get(path).json(),[])
    def test_unknowns_and_no_url_fetch(self):
        owner=self.owner()
        job=self.create(owner,{"label":"Any role","original_text":"Only evidence","source_url":"https://source.invalid/vacancy"})
        self.assertFalse(job["latest"]["association_confirmed"])
        unknown=self.create(owner,{"label":"Incomplete","original_text":"Job text"})
        self.assertIsNone(unknown["latest"]["source_url"])
        self.assertNotIn("career_role",unknown["latest"])
    def test_pagination_missing_owner(self):
        owner=self.owner(); job=self.create(owner); self.create(owner); path=f"/career/owners/{owner}/jobs"
        self.assertEqual(len(self.client.get(path+"?limit=1&offset=1").json()),1)
        self.assertEqual(self.client.get(path+"?limit=101").status_code,422)
        self.assertEqual(self.client.get(f"/career/owners/{uuid4()}/jobs").status_code,404)
        self.assertEqual(self.client.post(f"/career/owners/{uuid4()}/jobs",json=sample()).status_code,404)
    @unittest.skipUnless(fixtures.TEST_URL,"PostgreSQL required for row locks")
    def test_concurrent_captures(self):
        owner=self.owner(); job=self.create(owner); path=f"/career/owners/{owner}/jobs/{job['id']}/snapshots"
        def edit(_):
            with TestClient(self.app) as c: return c.post(path,json={**sample(),"expected_version":1}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(edit,range(2)))
        self.assertEqual(sorted(results),[201,409])
        self.assertEqual(len(self.client.get(path).json()),2)
if __name__=="__main__": unittest.main()
