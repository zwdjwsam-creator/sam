# -*- coding: utf-8 -*-
"""Offline cases the previous 8/32-hop exact-path audit mislabeled."""
import unittest

from link_resolve import RESOURCE_LIMIT, Graph


def _chain(length: int) -> Graph:
    graph = Graph()
    graph.add_directory(r"E:\BLACKBOX\end")
    graph.add_junction(rf"E:\BLACKBOX\n{length}", r"E:\BLACKBOX\end")
    for index in range(length, 0, -1):
        graph.add_junction(rf"E:\BLACKBOX\n{index - 1}", rf"E:\BLACKBOX\n{index}")
    return graph


class ResolveTests(unittest.TestCase):
    def test_finite_chain_longer_than_32_closes(self):
        graph = _chain(70)
        result = graph.resolve(r"E:\BLACKBOX\n0")
        self.assertEqual(result["class"], "CLOSED_DIRECTORY")
        self.assertEqual(result["terminal"], r"E:\BLACKBOX\end")
        self.assertGreater(result["chain_length"], 32)

    def test_true_cycle_is_not_called_missing(self):
        graph = Graph()
        graph.add_junction(r"E:\BLACKBOX\a", r"E:\BLACKBOX\b")
        graph.add_junction(r"E:\BLACKBOX\b", r"E:\BLACKBOX\a")
        result = graph.resolve(r"E:\BLACKBOX\a")
        self.assertEqual(result["class"], "CYCLE")

    def test_parent_junction_plus_child_suffix(self):
        graph = Graph()
        graph.add_junction(r"E:\BLACKBOX\A", r"E:\BLACKBOX\real")
        graph.add_directory(r"E:\BLACKBOX\real\child")
        result = graph.resolve(r"E:\BLACKBOX\A\child")
        self.assertEqual(result["class"], "CLOSED_DIRECTORY")
        self.assertEqual(result["terminal"], r"E:\BLACKBOX\real\child")
        self.assertEqual(result["replacements"][0]["reason"], "parent_junction_suffix")

    def test_migrated_engine_path_is_not_mapped_again(self):
        graph = Graph()
        link = r"E:\BLACKBOX_ENGINES\CURSOR_TASK_ARCHIVE\pit_products\data"
        target = r"E:\BLACKBOX\数据\cache\data"
        graph.add_junction(link, target)
        graph.add_directory(target)
        result = graph.resolve(link)
        self.assertEqual(result["class"], "CLOSED_DIRECTORY")
        self.assertTrue(result["terminal"].startswith(r"E:\BLACKBOX"))

    def test_directory_file_missing_and_escape_stay_distinct(self):
        graph = Graph()
        graph.add_directory(r"E:\BLACKBOX\dir")
        graph.add_file(r"E:\BLACKBOX\file")
        graph.add_junction(r"E:\BLACKBOX\out", r"F:\OLD\place")
        self.assertEqual(graph.resolve(r"E:\BLACKBOX\dir")["class"], "CLOSED_DIRECTORY")
        self.assertEqual(graph.resolve(r"E:\BLACKBOX\file")["class"], "TARGET_FILE")
        missing = graph.resolve(r"E:\BLACKBOX\absent\child")
        self.assertEqual(missing["class"], "MISSING_TERMINAL")
        self.assertEqual(missing["missing_ancestor"], r"E:\BLACKBOX\absent")
        self.assertEqual(graph.resolve(r"E:\BLACKBOX\out")["class"], "SCOPE_ESCAPE")

    def test_resource_limit_is_not_labeled_missing(self):
        graph = _chain(RESOURCE_LIMIT + 5)
        result = graph.resolve(r"E:\BLACKBOX\n0")
        self.assertEqual(result["class"], "UNRESOLVED_RESOURCE_LIMIT")


if __name__ == "__main__":
    unittest.main()
