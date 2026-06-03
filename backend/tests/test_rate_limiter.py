import unittest

from src.services.rate_limiter import RateLimitExceeded, RateLimiter


class RateLimiterTests(unittest.TestCase):
    def setUp(self):
        RateLimiter._memory_store.clear()

    def test_blocks_after_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60, connection_string=None)
        key = limiter.visitor_key("127.0.0.1", "test-agent")

        limiter.check(key)
        limiter.check(key)

        with self.assertRaises(RateLimitExceeded):
            limiter.check(key)


if __name__ == "__main__":
    unittest.main()
