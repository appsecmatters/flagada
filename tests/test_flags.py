import unittest

from routes.flags import _validate_value


class TestValidateValue(unittest.TestCase):
    def test_valid_hex64(self):
        self.assertIsNone(
            _validate_value("25c88484531cb506c602a0fd08f2ae88ff009781ac4d23b32665d3bdae4d567c")
        )


if __name__ == "__main__":
    unittest.main()
