import hashlib
import os
import tempfile
import unittest

import jwt

import db
from app import app

VALID_VALUE = "25c88484531cb506c602a0fd08f2ae88ff009781ac4d23b32665d3bdae4d567c"
TEST_SECRET = "test-secret"


def _make_token():
    return jwt.encode({"sub": "test"}, TEST_SECRET, algorithm="HS256")


class TestValidateFlag(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        db.DATABASE = self.db_path
        os.environ["ADMIN_SECRET"] = TEST_SECRET
        app.config["TESTING"] = True
        self.client = app.test_client()
        db.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)
        os.environ.pop("ADMIN_SECRET", None)

    def _auth(self):
        return {"Authorization": f"Bearer {_make_token()}"}

    def _post_flag(self, **kwargs):
        return self.client.post("/flags", json={"value": VALID_VALUE, "application_name": "app1", **kwargs}, headers=self._auth())

    def _hashed_value(self):
        return hashlib.sha256(VALID_VALUE.encode()).hexdigest()

    def test_found_when_flag_exists(self):
        self._post_flag()
        response = self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user1"})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["found"])
        self.assertNotIn("flag", body)

    def test_found_updates_status_owner_and_timestamp(self):
        self._post_flag()
        before = self.client.get(f"/flags/{self._hashed_value()}", headers=self._auth()).get_json()

        self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user42"})

        after = self.client.get(f"/flags/{self._hashed_value()}", headers=self._auth()).get_json()
        self.assertEqual(after["status"], "FOUND")
        self.assertEqual(after["owner"], "user42")
        self.assertGreater(after["updated_at"], before["updated_at"])

    def test_same_owner_already_submitted(self):
        self._post_flag()
        self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user1"})
        response = self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message"], "You already submitted this flag")

    def test_different_owner_already_submitted(self):
        self._post_flag()
        self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user1"})
        response = self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user2"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Someone else already submitted this flag on", response.get_json()["message"])

    def test_not_found_when_flag_absent(self):
        response = self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user1"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["found"])

    def test_invalid_value_returns_false(self):
        response = self.client.post("/validateFlag", json={"value": "notahex", "owner": "user1"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["found"])

    def test_deprecated_flag_returns_message(self):
        self._post_flag(status="DEPRECATED")
        response = self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message"], "Flag is outdated. Please try capturing its latest version")

    def test_deleted_flag_returns_false(self):
        self._post_flag()
        self.client.delete(f"/flags/{self._hashed_value()}", headers=self._auth())
        response = self.client.post("/validateFlag", json={"value": VALID_VALUE, "owner": "user1"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["found"])

    def test_missing_owner_returns_422(self):
        response = self.client.post("/validateFlag", json={"value": VALID_VALUE})
        self.assertEqual(response.status_code, 422)

    def test_missing_token_returns_401(self):
        response = self.client.get("/flags")
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_returns_401(self):
        response = self.client.get("/flags", headers={"Authorization": "Bearer badtoken"})
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
