#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and Integration Tests for SCMU Knowledge Base, Index, Golden Quotes, and Query CLI
"""

import os
import sys
import json
import subprocess
import unittest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB_DIR = os.path.join(PROJECT_DIR, "references", "scmu_knowledge_base")
CORPUS_PATH = os.path.join(KB_DIR, "scmu_articles_corpus.json")
INDEX_PATH = os.path.join(KB_DIR, "kb_index.json")
QUOTES_PATH = os.path.join(KB_DIR, "golden_quotes.json")
QUERY_SCRIPT = os.path.join(PROJECT_DIR, "scripts", "query_kb.py")


class TestSCMUKnowledgeBase(unittest.TestCase):
    """Corpus, Index, and Golden Quotes Data Integrity Tests"""

    def test_corpus_exists_and_valid(self):
        """Verify scmu_articles_corpus.json exists, has 278 articles and all mandatory fields."""
        self.assertTrue(os.path.isfile(CORPUS_PATH), f"Corpus file missing: {CORPUS_PATH}")
        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            corpus = json.load(f)
        self.assertEqual(len(corpus), 278, f"Expected 278 articles, got {len(corpus)}")
        
        mandatory_fields = ["title", "date", "source", "author", "url", "category", "content"]
        for idx, art in enumerate(corpus):
            for field in mandatory_fields:
                self.assertIn(field, art, f"Article {idx} missing mandatory field: {field}")
            self.assertTrue(art["title"].strip(), f"Article {idx} has empty title")
            self.assertTrue(art["content"].strip(), f"Article {idx} has empty content")
            self.assertTrue(art["url"].startswith("http"), f"Article {idx} has invalid URL: {art['url']}")

    def test_kb_index_structure(self):
        """Verify kb_index.json structure, inverted index, tags, and imagery keywords."""
        self.assertTrue(os.path.isfile(INDEX_PATH), f"Index file missing: {INDEX_PATH}")
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        self.assertIn("metadata", index_data)
        self.assertIn("categories", index_data)
        self.assertIn("tags", index_data)
        self.assertIn("imagery_keywords", index_data)
        self.assertIn("inverted_index", index_data)
        self.assertIn("articles", index_data)

        self.assertEqual(index_data["metadata"]["total_articles"], 278)

        # Check required imagery keywords
        required_imagery = ["双塔", "南湖", "石榴籽", "军训", "急救", "迷彩", "晨曦", "晚霞", "绿茵", "汗水"]
        for kw in required_imagery:
            self.assertIn(kw, index_data["imagery_keywords"], f"Imagery keyword missing: {kw}")
            self.assertIn(kw, index_data["inverted_index"], f"Inverted index keyword missing: {kw}")

        # Check categories
        self.assertIn("军训", index_data["categories"])
        self.assertIn("迎新", index_data["categories"])
        self.assertIn("计算机", index_data["categories"])
        self.assertEqual(index_data["categories"]["军训"]["count"], 30)

        # Check tags
        self.assertIn("军训淬炼", index_data["tags"])
        self.assertIn("民族团结", index_data["tags"])
        self.assertIn("南湖风物", index_data["tags"])
        self.assertIn("青春奋斗", index_data["tags"])
        self.assertIn("校训精神", index_data["tags"])

    def test_golden_quotes_structure_and_provenance(self):
        """Verify golden_quotes.json themes, structure, and exact provenance URLs."""
        self.assertTrue(os.path.isfile(QUOTES_PATH), f"Quotes file missing: {QUOTES_PATH}")
        with open(QUOTES_PATH, "r", encoding="utf-8") as f:
            quotes_data = json.load(f)

        self.assertIn("metadata", quotes_data)
        self.assertIn("themes", quotes_data)
        self.assertIn("quotes_by_theme", quotes_data)
        self.assertIn("quotes", quotes_data)

        self.assertGreaterEqual(quotes_data["metadata"]["total_quotes"], 40)
        self.assertGreaterEqual(len(quotes_data["themes"]), 5)

        required_themes = ["军训淬炼", "南湖风物", "民族团结", "青春奋斗", "校训精神"]
        for th in required_themes:
            self.assertIn(th, quotes_data["themes"], f"Required theme missing: {th}")

        # Provenance verification on all quotes
        for q in quotes_data["quotes"]:
            self.assertTrue(q["id"].startswith("GQ-"), f"Invalid quote ID: {q['id']}")
            self.assertTrue(q["quote"].strip(), f"Quote text empty: {q['id']}")
            self.assertTrue(q["article_title"].strip(), f"Quote missing article title: {q['id']}")
            self.assertTrue(q["date"].strip(), f"Quote missing date: {q['id']}")
            self.assertTrue(q["url"].startswith("http"), f"Quote missing valid URL: {q['id']}")
            self.assertIsInstance(q["article_id"], int, f"Quote missing integer article_id: {q['id']}")


class TestQueryKBCli(unittest.TestCase):
    """CLI Execution Tests for scripts/query_kb.py"""

    def run_cli(self, args, expect_code=0):
        cmd = [sys.executable, QUERY_SCRIPT] + args
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(result.returncode, expect_code, f"CLI exited with {result.returncode}, stderr: {result.stderr}")
        return result.stdout

    def test_cli_stats(self):
        """Test --stats displays formatted knowledge base summary."""
        out = self.run_cli(["--stats"])
        self.assertIn("中南民族大学官方语料知识库全景统计报表", out)
        self.assertIn("278", out)
        self.assertIn("军训", out)
        self.assertIn("双塔", out)
        self.assertIn("南湖", out)
        self.assertIn("石榴籽", out)

    def test_cli_stats_json(self):
        """Test --stats --json produces parseable JSON."""
        out = self.run_cli(["--stats", "--json"])
        data = json.loads(out)
        self.assertEqual(data["total_articles"], 278)
        self.assertIn("categories", data)
        self.assertIn("imagery_keywords", data)
        self.assertIn("golden_quotes", data)

    def test_cli_query_shuangta(self):
        """Test searching '双塔' returns articles and URLs."""
        out = self.run_cli(["--query", "双塔", "--limit", "3"])
        self.assertIn("双塔", out)
        self.assertIn("http", out)
        self.assertIn("发布日期", out)

    def test_cli_query_nanhu(self):
        """Test searching '南湖' returns multiple articles."""
        out = self.run_cli(["--query", "南湖", "--limit", "5"])
        self.assertIn("南湖", out)
        self.assertIn("http", out)

    def test_cli_query_shiliuzi_json(self):
        """Test searching '石榴籽' with --json."""
        out = self.run_cli(["--query", "石榴籽", "--json", "--limit", "3"])
        data = json.loads(out)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["query"], "石榴籽")
        self.assertGreater(data["total_matches"], 0)
        first = data["results"][0]
        self.assertIn("title", first)
        self.assertIn("url", first)
        self.assertIn("snippets", first)

    def test_cli_category_filter(self):
        """Test filtering by category '军训'."""
        out = self.run_cli(["--category", "军训", "--limit", "3", "--json"])
        data = json.loads(out)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["category"], "军训")
        self.assertGreater(data["total_matches"], 0)
        for item in data["results"]:
            self.assertEqual(item["category"], "军训")

    def test_cli_tag_filter(self):
        """Test filtering by tag '民族团结'."""
        out = self.run_cli(["--tag", "民族团结", "--limit", "3", "--json"])
        data = json.loads(out)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["tag"], "民族团结")
        self.assertGreater(data["total_matches"], 0)
        for item in data["results"]:
            self.assertIn("民族团结", item["tags"])

    def test_cli_quotes_retrieval(self):
        """Test retrieving quotes and theme filtering."""
        out = self.run_cli(["--quotes", "--theme", "军训淬炼", "--limit", "5"])
        self.assertIn("军训淬炼", out)
        self.assertIn("迷彩铸魂抒壮志", out)
        self.assertIn("原文溯源链接", out)

    def test_cli_quotes_query_filter(self):
        """Test querying quotes with keyword '迷彩'."""
        out = self.run_cli(["--quotes", "--query", "迷彩"])
        self.assertIn("迷彩", out)
        self.assertIn("GQ-001", out)

    def test_cli_golden_quotes_alias(self):
        """Test --golden-quotes flag alias."""
        out = self.run_cli(["--golden-quotes", "--limit", "2", "--json"])
        data = json.loads(out)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["type"], "golden_quotes")
        self.assertEqual(len(data["quotes"]), 2)

    def test_cli_strict_mode(self):
        """Test strict mode returns exit code 1 on 0 matches."""
        # Non-strict mode should return code 0
        self.run_cli(["--query", "NON_EXISTENT_KEYWORD_XYZ_98765"], expect_code=0)
        # Strict mode should return code 1
        self.run_cli(["--query", "NON_EXISTENT_KEYWORD_XYZ_98765", "--strict"], expect_code=1)

    def test_cli_empty_query(self):
        """Test empty query parameter behaves gracefully without error."""
        out = self.run_cli(["--query", ""])
        self.assertIn("SCMU KB Statistics", out)

    def test_cli_no_highlight_flag(self):
        """Test --no-highlight flag prevents ANSI codes."""
        out = self.run_cli(["--query", "双塔", "--no-highlight", "--limit", "2"])
        self.assertNotIn("\033[1;33m", out)
        self.assertNotIn("\033[0m", out)


if __name__ == "__main__":
    unittest.main()
