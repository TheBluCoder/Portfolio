import unittest

from src.services.gallery_service import GalleryService


class GalleryServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        GalleryService._memory_poems.clear()
        GalleryService._memory_comments.clear()
        GalleryService._memory_likes.clear()

    def test_comment_is_hidden_until_approved(self) -> None:
        service = GalleryService(connection_string=None)
        poem = service.create_poem("Night", "A quiet line", None, ["poem"])
        comment = service.add_comment(poem["id"], "Reader", "Lovely", "visitor")

        self.assertEqual(service.list_poems()[0]["comments"], [])

        service.moderate_comment(comment["id"], True)

        self.assertEqual(len(service.list_poems()[0]["comments"]), 1)

    def test_like_counts_once_per_visitor(self) -> None:
        service = GalleryService(connection_string=None)
        poem = service.create_poem("Night", "A quiet line", None, [])

        first = service.like_poem(poem["id"], "visitor")
        second = service.like_poem(poem["id"], "visitor")

        self.assertEqual(first["likes"], 1)
        self.assertEqual(second["likes"], 1)


if __name__ == "__main__":
    unittest.main()
