import unittest
from unittest.mock import patch

import pandas as pd

import analyzer


class ColumnSelectionTests(unittest.TestCase):
    def test_social_text_column_precedes_generic_text(self):
        columns = ["id", "text", "Tweet_Text", "created_at"]

        self.assertEqual(analyzer.default_text_column(columns), "Tweet_Text")

    def test_alias_normalization_handles_spacing_and_punctuation(self):
        self.assertEqual(analyzer.normalize_column_name(" Full-Text "), "full text")
        self.assertEqual(analyzer.normalize_column_name("REVIEW_TEXT"), "review text")

    def test_blank_rows_are_removed_without_mutating_input(self):
        dataframe = pd.DataFrame(
            {
                "tweet_text": ["first", None, "   ", "last"],
                "id": [1, 2, 3, 4],
            }
        )

        filtered = analyzer.non_empty_text_rows(dataframe, "tweet_text")

        self.assertEqual(filtered["id"].tolist(), [1, 4])
        self.assertEqual(len(dataframe), 4)


class StartupTests(unittest.TestCase):
    def tearDown(self):
        analyzer.engine = None

    def test_import_does_not_create_a_gui_or_engine(self):
        self.assertIsNone(analyzer.root)
        self.assertIsNone(analyzer.engine)

    def test_missing_vader_data_is_downloaded_on_first_use(self):
        sentinel = object()
        with (
            patch.object(
                analyzer,
                "SentimentEngine",
                side_effect=[LookupError("missing"), sentinel],
            ) as engine_class,
            patch.object(analyzer.nltk, "download") as download,
        ):
            self.assertIs(analyzer.get_engine(), sentinel)

        self.assertEqual(engine_class.call_count, 2)
        download.assert_called_once_with("vader_lexicon", quiet=True)


class ThreadErrorTests(unittest.TestCase):
    def tearDown(self):
        analyzer.root = None

    def test_queued_error_callback_preserves_the_exception_message(self):
        class ImmediateRoot:
            @staticmethod
            def after(_delay, callback):
                callback()

        analyzer.root = ImmediateRoot()
        dataframe = pd.DataFrame({"text": ["example"]})

        with patch.object(analyzer.messagebox, "showerror") as showerror:
            analyzer.run_analysis_thread(
                dataframe,
                "missing",
                "reviews.csv",
                object(),
                object(),
            )

        showerror.assert_called_once_with("Error", "'missing'")


if __name__ == "__main__":
    unittest.main()
