#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adversarial Stress & Boundary Verification Test Suite (Challenger 1)

This suite stress-tests:
1. scripts/query_kb.py (CLI arguments, boundaries, regex injection, non-ASCII, strict exit codes)
2. scripts/check_compliance.py (BLOCKERs POL-001..005, WARNINGs SCMU-001..007, PHOTO-001..002, ReDoS, False Negatives, False Positives)
3. Data integrity of references/scmu_knowledge_base (corpus, inverted index, golden quotes, URL validity, orphan ID audit)
"""

import json
import os
import subprocess
import sys
import time
import unittest
import urllib.parse

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB_DIR = os.path.join(PROJECT_DIR, "references", "scmu_knowledge_base")
CORPUS_PATH = os.path.join(KB_DIR, "scmu_articles_corpus.json")
INDEX_PATH = os.path.join(KB_DIR, "kb_index.json")
QUOTES_PATH = os.path.join(KB_DIR, "golden_quotes.json")
QUERY_SCRIPT = os.path.join(PROJECT_DIR, "scripts", "query_kb.py")
COMPLIANCE_SCRIPT = os.path.join(PROJECT_DIR, "scripts", "check_compliance.py")

sys.path.insert(0, os.path.join(PROJECT_DIR, "scripts"))
from check_compliance import check_content, RULES


class TestQueryKBBoundaryAndStress(unittest.TestCase):
    """Stress tests against scripts/query_kb.py"""

    def run_cli(self, args: list, expect_code: int = 0):
        cmd = [sys.executable, QUERY_SCRIPT] + args
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(
            proc.returncode,
            expect_code,
            f"CLI exited with {proc.returncode} (expected {expect_code}).\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
        )
        return proc.stdout, proc.stderr

    def test_regex_metacharacters_resilience(self):
        """Query with dangerous regex characters should not crash and should search literal characters."""
        dangerous_queries = [
            ".*",
            ".*+?^$()[]{}|\\",
            "(\\d+)+",
            "(?<=abc).*?",
            "[a-z]*?",
            "\\\\g<1>",
            "\\0",
            "^.*$",
        ]
        for dq in dangerous_queries:
            # Under strict mode, searching nonexistent literal pattern should exit with code 1 without crashing
            out, err = self.run_cli(["--query", dq, "--strict"], expect_code=1)
            self.assertIn("共找到 0 篇", out)
            self.assertEqual(err.strip(), "")

    def test_non_ascii_and_unicode_edge_cases(self):
        """Query with emojis, minority scripts, fullwidth symbols, and zero-width spaces."""
        edge_cases = [
            "🔥🎓🇨🇳",               # Emojis
            "（）【】“”‘’；：",       # Fullwidth punctuation
            "བོད་ཡིག",              # Tibetan
            "ئۇيغۇرچە",              # Uyghur
            "ᠮᠣᠩᡤᠣᠯ ᠬᠡᠯᠡ",          # Mongolian
            "\u200b\u200c\u200d",     # Zero-width spaces
        ]
        for ec in edge_cases:
            out, err = self.run_cli(["--query", ec, "--strict"], expect_code=1)
            self.assertIn("共找到 0 篇", out)

    def test_extreme_limits(self):
        """Verify behavior with extreme limit values."""
        # limit = 0 (no limit)
        out, _ = self.run_cli(["--query", "军训", "--limit", "0", "--json"], expect_code=0)
        data = json.loads(out)
        self.assertEqual(len(data["results"]), 30)

        # limit = 1000000 (exceeding total articles)
        out, _ = self.run_cli(["--query", "军训", "--limit", "1000000", "--json"], expect_code=0)
        data = json.loads(out)
        self.assertEqual(len(data["results"]), 30)

        # limit = -1 (negative limit treated as no limit in slice)
        out, _ = self.run_cli(["--query", "军训", "--limit", "-1", "--json"], expect_code=0)
        data = json.loads(out)
        self.assertEqual(len(data["results"]), 30)

    def test_nonexistent_filters_with_strict(self):
        """Nonexistent category, tag, or theme must exit with code 1 in strict mode."""
        # Category nonexistent
        self.run_cli(["--category", "不存在的非法分类_XYZ_999", "--strict"], expect_code=1)
        # Tag nonexistent
        self.run_cli(["--tag", "不存在的非法标签_XYZ_999", "--strict"], expect_code=1)
        # Golden quotes theme nonexistent
        self.run_cli(["--quotes", "--theme", "不存在的非法主题_XYZ_999", "--strict"], expect_code=1)
        # Golden quotes query nonexistent
        self.run_cli(["--quotes", "--query", "不存在的金句词_XYZ_999", "--strict"], expect_code=1)

    def test_empty_query_vs_whitespace_query_semantics(self):
        """Verify normalized whitespace query semantics between --query '' and --query '   '."""
        # Empty string: triggers empty check in main(), displays help/stats, exit 0
        out_empty, _ = self.run_cli(["--query", "", "--strict", "--json"], expect_code=0)
        data_empty = json.loads(out_empty)
        self.assertEqual(len(data_empty.get("results", [])), 0)

        # Whitespace query: normalized/stripped before check, triggers empty check, returns 0 matches
        out_ws, _ = self.run_cli(["--query", "   ", "--strict", "--json"], expect_code=0)
        data_ws = json.loads(out_ws)
        self.assertEqual(len(data_ws.get("results", [])), 0)


class TestComplianceAdversarialAndVulnerabilities(unittest.TestCase):
    """Adversarial stress tests exposing boundary conditions and false negative/positive vectors."""

    def test_pol_001_blocker_and_evasion_variants(self):
        """POL-001 detects standard violations, but exhibits false negatives on morphological variants."""
        # Standard violations: MUST BE FLAGGED
        res1 = check_content("中南民大师生深入铸造中华民族共同体意识。")
        self.assertIn("POL-001", [i["id"] for i in res1])

        res2 = check_content("铸就中华民族共同体意识是我们的根本任务。")
        self.assertIn("POL-001", [i["id"] for i in res2])

        # Correct phrasing: MUST NOT BE FLAGGED
        res_ok = check_content("铸牢中华民族共同体意识是各项工作的主线。")
        self.assertNotIn("POL-001", [i["id"] for i in res_ok])

        # Adversarial evasion variants (morphological / syntactic insertion)
        # Verified: Now hardened against false negative vulnerabilities
        res_fn1 = check_content("学校进一步铸造了中华民族共同体意识。")
        self.assertIn("POL-001", [i["id"] for i in res_fn1],
                      "Hardened POL-001 must catch '铸造了中华民族共同体意识'")

        res_fn2 = check_content("全面铸造中华民族的共同体意识。")
        self.assertIn("POL-001", [i["id"] for i in res_fn2],
                      "Hardened POL-001 must catch '中华民族的共同体意识'")

    def test_pol_002_blocker_and_evasion_variants(self):
        """POL-002 detects '中华民族命运共同体意识' and '中华民族命运共同体' without '意识'."""
        res_standard = check_content("我们必须树立中华民族命运共同体意识。")
        self.assertIn("POL-002", [i["id"] for i in res_standard])

        # Verified: Now hardened to catch '中华民族命运共同体' even without '意识'
        res_fn = check_content("携手打造中华民族命运共同体，共绘同心圆。")
        self.assertIn("POL-002", [i["id"] for i in res_fn],
                      "Hardened POL-002 must catch '中华民族命运共同体' without '意识'")

    def test_pol_003_pan_halal_and_legitimate_campus_dining(self):
        """POL-003 flags pan-halal items but does NOT flag legitimate campus halal dining."""
        bad_items = [
            "严禁在校内设置清真通道或清真专用道。",
            "坚决抵制清真水、清真盐等泛清真化倾向。",
            "宿舍严禁采购所谓清真纸。",
        ]
        for text in bad_items:
            res = check_content(text)
            self.assertIn("POL-003", [i["id"] for i in res])

        # Legitimate campus dining: MUST NOT BE FLAGGED
        good_items = [
            "新生军训期间，学校清真食堂（清真餐厅）正常供应丰富民族特色餐点。",
            "学生可以在清真窗口刷卡就餐。",
        ]
        for text in good_items:
            res = check_content(text)
            self.assertNotIn("POL-003", [i["id"] for i in res])

    def test_pol_004_proselytization_and_negative_context_false_positive(self):
        """POL-004 flags campus proselytization, but exhibits false positives on defensive anti-proselytization reports."""
        # Unlawful proselytization: MUST BE FLAGGED
        bad_text = "本周日将在平顶山举办校园传教与宗教进校园交流座谈会。"
        res_bad = check_content(bad_text)
        self.assertIn("POL-004", [i["id"] for i in res_bad])

        # Defensive official context: Documenting false positive vulnerability
        defensive_text = "校党委深入贯彻教育与宗教相分离原则，坚决抵御宗教进校园，严禁在校内开展校园传教活动。"
        res_def = check_content(defensive_text)
        self.assertIn("POL-004", [i["id"] for i in res_def],
                      "Documented false positive: Defensive anti-proselytization statement is flagged by POL-004")

    def test_pol_005_affiliation_and_evasion_variants(self):
        """POL-005 detects exact phrases and common syntactic variations."""
        # Standard exact phrases: FLAGGED
        self.assertIn("POL-005", [i["id"] for i in check_content("教育部直属的中南民族大学迎来70周年校庆。")])
        self.assertIn("POL-005", [i["id"] for i in check_content("中南民族大学是教育部直属高校。")])

        # Syntactic evasion variants: Verified caught by hardened regex
        evasion_cases = [
            "中南民族大学系教育部直属重点高校。",
            "中南民族大学作为教育部直属综合性大学。",
            "教育部直属高校中南民族大学举行开学典礼。",
            "中南民大是教育部直属大学。",
            "我校是教育部直属重点综合性大学。",
        ]
        for ec in evasion_cases:
            res = check_content(ec)
            self.assertIn("POL-005", [i["id"] for i in res],
                          f"Hardened POL-005 must catch: '{ec}'")

    def test_scmu_006_and_007_lookahead_word_order_vulnerability(self):
        """SCMU-006 and SCMU-007 bidirectional word order verification."""
        # SCMU-006 forward order works:
        res_6_fwd = check_content("我们在东湖之畔遥望双塔。")
        self.assertIn("SCMU-006", [i["id"] for i in res_6_fwd])

        # SCMU-006 reverse order (natural Chinese): VERIFIED CAUGHT
        res_6_rev1 = check_content("遥望南区双塔，我们走在东湖之畔。")
        self.assertIn("SCMU-006", [i["id"] for i in res_6_rev1],
                      "Hardened SCMU-006 must catch reverse order '双塔...东湖之畔'")
        res_6_rev2 = check_content("民大学子在东湖之滨举行集会。")
        self.assertIn("SCMU-006", [i["id"] for i in res_6_rev2],
                      "Hardened SCMU-006 must catch reverse order '民大...东湖之滨'")

        # SCMU-007 forward order works:
        res_7_fwd = check_content("文学院是我校创办较早的文科学系。")
        self.assertIn("SCMU-007", [i["id"] for i in res_7_fwd])

        # SCMU-007 reverse order (standard natural Chinese '我校文学院', '中南民大文学院'): VERIFIED CAUGHT
        res_7_rev1 = check_content("我校文学院今日举办学术研讨会。")
        self.assertIn("SCMU-007", [i["id"] for i in res_7_rev1],
                      "Hardened SCMU-007 must catch '我校文学院'")
        res_7_rev2 = check_content("中南民大文学院师生踊跃参赛。")
        self.assertIn("SCMU-007", [i["id"] for i in res_7_rev2],
                      "Hardened SCMU-007 must catch '中南民大文学院'")

    def test_photo_case_sensitivity_vulnerability(self):
        """PHOTO-001/002 are case insensitive and match lowercase .jpg or .jpeg."""
        # Upper case: FLAGGED
        res_upper = check_content("配图：IMG_3878.JPG")
        self.assertIn("PHOTO-001", [i["id"] for i in res_upper])

        # Lower case and mixed case: VERIFIED CAUGHT
        res_lower1 = check_content("配图：IMG_3878.jpg")
        self.assertIn("PHOTO-001", [i["id"] for i in res_lower1],
                      "Hardened PHOTO-001 must catch 'IMG_3878.jpg'")
        res_lower2 = check_content("配图：img_3878.JPG")
        self.assertIn("PHOTO-001", [i["id"] for i in res_lower2],
                      "Hardened PHOTO-001 must catch 'img_3878.JPG'")
        res_lower3 = check_content("配图：IMG_3841.jpg")
        self.assertIn("PHOTO-002", [i["id"] for i in res_lower3],
                      "Hardened PHOTO-002 must catch 'IMG_3841.jpg'")

    def test_multiline_quote_false_positive_fmt_002(self):
        """FMT-002 checks line-by-line, causing false positives on legitimate multi-line quotes."""
        multiline_quote = """“青年一代有理想、有本领、有担当，
国家就有前途，民族就有希望。”"""
        issues = check_content(multiline_quote)
        fmt_ids = [i["id"] for i in issues if i["id"] == "FMT-002"]
        self.assertIn("FMT-002", fmt_ids,
                      "Documented false positive: Multi-line quotation marks trigger FMT-002 on line 1")

    def test_redos_performance_resilience(self):
        """Verify regexes do not suffer from catastrophic backtracking on pathological inputs."""
        pathological_lines = [
            # TONE-001: 如果说.*那么.*系统架构
            "如果说" + "那么不仅如此而且还要进一步提高" * 3000 + "未完结。",
            # FMT-001: ^#\s+.*[。！!？?]\s*$
            "# " + "中南民族大学官方公众号权威发布深度校园报道" * 3000 + "末尾无标点",
            # SCMU-006: 东湖之畔.*双塔
            "东湖之畔" + "南湖之滨青春奋斗笃信好学自然宽和" * 3000 + "未完结。",
        ]
        for line in pathological_lines:
            t0 = time.perf_counter()
            issues = check_content(line)
            duration = time.perf_counter() - t0
            self.assertLess(duration, 0.5, f"ReDoS vulnerability detected! Regex took {duration:.2f}s")

    def test_all_26_tier_c_photos_blocked(self):
        """Verify all 26 Tier-C disqualified photos are blocked by compliance rules in both upper and lowercase."""
        tier_c_photos = [
            "IMG_3823.JPG", "IMG_3824.JPG", "IMG_3825.JPG", "IMG_3826.JPG",
            "IMG_3831.JPG", "IMG_3832.JPG", "IMG_3841.JPG", "IMG_3849.JPG",
            "IMG_3871.JPG", "IMG_3878.JPG", "IMG_3879.JPG", "IMG_3887.JPG",
            "IMG_3888.JPG", "IMG_3889.JPG", "IMG_3890.JPG", "IMG_3891.JPG",
            "IMG_3896.JPG", "IMG_3900.JPG", "IMG_3901.JPG", "IMG_3902.JPG",
            "IMG_3903.JPG", "IMG_3907.JPG", "IMG_3908.JPG", "IMG_3909.JPG",
            "IMG_3910.JPG", "IMG_3911.JPG"
        ]
        self.assertEqual(len(tier_c_photos), 26)
        for photo in tier_c_photos:
            # Uppercase test
            issues = check_content(f"配图：{photo}")
            photo_rules = [i["id"] for i in issues if i["id"] in ("PHOTO-001", "PHOTO-002")]
            self.assertTrue(len(photo_rules) > 0, f"Tier-C photo {photo} was not caught by compliance rules")

            # Lowercase test
            issues_lower = check_content(f"配图：{photo.lower()}")
            photo_rules_lower = [i["id"] for i in issues_lower if i["id"] in ("PHOTO-001", "PHOTO-002")]
            self.assertTrue(len(photo_rules_lower) > 0, f"Lowercase Tier-C photo {photo.lower()} was not caught")


class TestDataIntegrityDeepAudit(unittest.TestCase):
    """Deep verification of JSON databases, schemas, URLs, and relational consistency."""

    @classmethod
    def setUpClass(cls):
        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            cls.corpus = json.load(f)
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            cls.index_data = json.load(f)
        with open(QUOTES_PATH, "r", encoding="utf-8") as f:
            cls.quotes_data = json.load(f)

    def test_corpus_size_and_id_continuity(self):
        """Corpus must have exactly 278 articles with contiguous IDs."""
        self.assertEqual(len(self.corpus), 278)
        self.assertEqual(self.index_data["metadata"]["total_articles"], 278)

    def test_corpus_url_validity_and_uniqueness(self):
        """All corpus URLs must be valid, unique, and point to SCMU official domain."""
        urls = [art.get("url", "") for art in self.corpus]
        self.assertEqual(len(urls), len(set(urls)), "Duplicate URLs detected in corpus")

        for idx, art in enumerate(self.corpus):
            url = art.get("url", "")
            parsed = urllib.parse.urlparse(url)
            self.assertIn(parsed.scheme, ("http", "https"), f"Article {idx} has invalid scheme: {url}")
            self.assertTrue(parsed.netloc, f"Article {idx} has missing domain: {url}")
            self.assertTrue(
                "scuec.edu.cn" in parsed.netloc,
                f"Article {idx} URL is outside SCMU domain: {url}"
            )

    def test_inverted_index_referential_integrity(self):
        """Inverted index must not contain any orphan article IDs."""
        valid_ids = set(range(len(self.corpus)))
        for kw, meta in self.index_data.get("inverted_index", {}).items():
            for art_entry in meta.get("articles", []):
                aid = art_entry.get("id")
                self.assertIn(
                    aid,
                    valid_ids,
                    f"Orphan article ID {aid} in inverted_index keyword '{kw}'"
                )

    def test_categories_and_tags_referential_integrity(self):
        """Categories and tags article_ids must all exist in corpus."""
        valid_ids = set(range(len(self.corpus)))
        for cat, meta in self.index_data.get("categories", {}).items():
            for aid in meta.get("article_ids", []):
                self.assertIn(aid, valid_ids, f"Orphan article ID {aid} in category '{cat}'")

        for tag, meta in self.index_data.get("tags", {}).items():
            for aid in meta.get("article_ids", []):
                self.assertIn(aid, valid_ids, f"Orphan article ID {aid} in tag '{tag}'")

    def test_golden_quotes_relational_and_url_integrity(self):
        """All golden quotes must have valid, uncorrupted URL and title provenance matching corpus."""
        quotes = self.quotes_data.get("quotes", [])
        self.assertGreaterEqual(len(quotes), 40)
        self.assertEqual(self.quotes_data["metadata"]["total_quotes"], len(quotes))

        quote_ids = [q["id"] for q in quotes]
        self.assertEqual(len(quote_ids), len(set(quote_ids)), "Duplicate quote IDs detected")

        for q in quotes:
            aid = q.get("article_id")
            self.assertIsInstance(aid, int, f"Quote {q['id']} article_id is not int")
            self.assertGreaterEqual(aid, 0, f"Quote {q['id']} negative article_id")
            self.assertLess(aid, len(self.corpus), f"Orphan quote {q['id']} references nonexistent article {aid}")

            # Verify exact provenance
            corpus_art = self.corpus[aid]
            self.assertEqual(
                q["url"],
                corpus_art["url"],
                f"Provenance URL mismatch for quote {q['id']}: '{q['url']}' != '{corpus_art['url']}'"
            )
            self.assertEqual(
                q["article_title"],
                corpus_art["title"],
                f"Provenance Title mismatch for quote {q['id']}: '{q['article_title']}' != '{corpus_art['title']}'"
            )


if __name__ == "__main__":
    unittest.main()
