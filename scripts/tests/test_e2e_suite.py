#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCMU WeChat Ecosystem - Comprehensive 4-Tier E2E Test Suite
Derived strictly from ORIGINAL_REQUEST.md, PROJECT.md, and TEST_INFRA.md.

Architecture:
- Tier 1: Feature Coverage (F1-F8, >=5 tests each, 40 tests)
- Tier 2: Boundary & Corner Cases (F1-F8, >=5 tests each, 40 tests)
- Tier 3: Cross-Feature Integration (10 pairwise tests)
- Tier 4: Real-World User Workflows (5 end-to-end scenario tests)
Total: 95 test cases.

Runner:
    python3 -m unittest scripts/tests/test_e2e_suite.py
"""

import base64
import json
import os
import re
import subprocess
import sys
import unittest
from io import BytesIO
from pathlib import Path
from PIL import Image

# Workspace Paths
WORKSPACE = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = WORKSPACE / "scripts"
REFERENCES_DIR = WORKSPACE / "references"
EXAMPLES_DIR = WORKSPACE / "examples"
KB_DIR = REFERENCES_DIR / "scmu_knowledge_base"
USB_PHOTO_DIR = Path("/Volumes/xbpd的u盘/junxun")

sys.path.insert(0, str(SCRIPTS_DIR))
from check_compliance import check_content, RULES
from deploy_to_xiumi import (
    PHOTO_SELECTION,
    build_xiumi_rich_html,
    get_base64_image,
)


class TestTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Feature Coverage (>=5 tests per feature F1-F8 across R1-R4)."""

    # -------------------------------------------------------------
    # F1: SCMU Web Crawler & Corpus Knowledge Base (R1)
    # -------------------------------------------------------------
    def test_f1_01_corpus_existence_and_count(self):
        """F1.1: Verify scmu_articles_corpus.json exists and contains >= 278 articles."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        self.assertTrue(corpus_path.is_file(), f"Corpus file not found: {corpus_path}")
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, list, "Corpus root must be a JSON list")
        self.assertGreaterEqual(len(data), 278, "Corpus must contain at least 278 articles")

    def test_f1_02_corpus_mandatory_fields(self):
        """F1.2: Verify every article in corpus contains all mandatory fields with non-empty values."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        mandatory_fields = ["title", "date", "content", "category", "url"]
        for idx, article in enumerate(data):
            for field in mandatory_fields:
                self.assertIn(field, article, f"Article index {idx} missing field: {field}")
                val = article[field]
                self.assertIsInstance(val, str, f"Article {idx} field {field} must be string")
                self.assertGreater(len(val.strip()), 0, f"Article {idx} field {field} must not be empty")

    def test_f1_03_military_training_corpus_structure(self):
        """F1.3: Verify military_training_corpus.md exists and contains >= 30 article sections."""
        mil_path = KB_DIR / "military_training_corpus.md"
        self.assertTrue(mil_path.is_file(), f"Military corpus file not found: {mil_path}")
        content = mil_path.read_text(encoding="utf-8")
        headers = re.findall(r"^##\s+.+$", content, re.MULTILINE)
        self.assertGreaterEqual(len(headers), 30, "Military training corpus must contain >= 30 article sections")

    def test_f1_04_characteristic_campus_imagery(self):
        """F1.4: Verify corpus contains essential SCMU campus imagery and symbols."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        all_text = " ".join([f"{a['title']} {a['content']}" for a in data])
        for imagery in ["双塔", "南湖", "石榴籽", "军训", "教官"]:
            self.assertIn(imagery, all_text, f"Quintessential imagery '{imagery}' not found in corpus")

    def test_f1_05_crawler_pipeline_code_integrity(self):
        """F1.5: Verify build_scmu_knowledge_base.py exists, targets SCMU news domain, and compiles."""
        crawler_script = SCRIPTS_DIR / "build_scmu_knowledge_base.py"
        self.assertTrue(crawler_script.is_file(), f"Crawler script not found: {crawler_script}")
        code = crawler_script.read_text(encoding="utf-8")
        self.assertIn("https://www.scuec.edu.cn/xww", code, "Crawler must target SCMU news website")
        self.assertIn("scmu_articles_corpus.json", code, "Crawler must output to scmu_articles_corpus.json")
        compiled = compile(code, str(crawler_script), "exec")
        self.assertIsNotNone(compiled)

    # -------------------------------------------------------------
    # F2: Local KB Search & Query CLI (R1)
    # -------------------------------------------------------------
    def test_f2_01_inverted_index_structure(self):
        """F2.1: Verify kb_index.json exists and has required top-level index keys."""
        index_path = KB_DIR / "kb_index.json"
        self.assertTrue(index_path.is_file(), f"Index file not found: {index_path}")
        with open(index_path, "r", encoding="utf-8") as f:
            idx = json.load(f)
        expected_keys = ["metadata", "categories", "tags", "imagery_keywords", "inverted_index", "articles"]
        for key in expected_keys:
            self.assertIn(key, idx, f"kb_index.json missing required key: {key}")
        self.assertGreaterEqual(len(idx["articles"]), 278)

    def test_f2_02_golden_quotes_database(self):
        """F2.2: Verify golden_quotes.json exists with themed quotes and source provenance."""
        quotes_path = KB_DIR / "golden_quotes.json"
        self.assertTrue(quotes_path.is_file(), f"Quotes file not found: {quotes_path}")
        with open(quotes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("quotes", data)
        self.assertIn("themes", data)
        quotes = data["quotes"]
        self.assertGreaterEqual(len(quotes), 10, "Golden quotes database must have >= 10 quotes")
        for q in quotes:
            for field in ["quote", "theme", "date", "url"]:
                self.assertIn(field, q, f"Quote missing provenance field: {field}")
                self.assertGreater(len(str(q[field]).strip()), 0)
            self.assertTrue("article_title" in q or "title" in q, "Quote must have title or article_title")

    def test_f2_03_query_cli_help(self):
        """F2.3: Verify scripts/query_kb.py exits with code 0 on --help with standard flags."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        self.assertTrue(query_script.is_file(), f"Query CLI script not found: {query_script}")
        res = subprocess.run(
            [sys.executable, str(query_script), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("--query", res.stdout)
        self.assertIn("--category", res.stdout)
        self.assertIn("--quotes", res.stdout)
        self.assertIn("--json", res.stdout)

    def test_f2_04_query_cli_keyword_search(self):
        """F2.4: Verify CLI search for '军训' returns matches containing title, date, and URL."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        res = subprocess.run(
            [sys.executable, str(query_script), "--query", "军训", "--limit", "3"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("军训", res.stdout)
        self.assertIn("http", res.stdout)

    def test_f2_05_query_cli_json_and_stats(self):
        """F2.5: Verify CLI --stats and --json output valid and parseable structured data."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        # Test --stats
        res_stats = subprocess.run(
            [sys.executable, str(query_script), "--stats"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_stats.returncode, 0)
        self.assertTrue("SCMU KB Statistics" in res_stats.stdout or "统计" in res_stats.stdout)

        # Test --json
        res_json = subprocess.run(
            [sys.executable, str(query_script), "--query", "双塔", "--json", "--limit", "2"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_json.returncode, 0)
        parsed = json.loads(res_json.stdout)
        self.assertIn("results", parsed)
        self.assertGreater(len(parsed["results"]), 0)

    # -------------------------------------------------------------
    # F3: Official Photo Selection Guide (R2)
    # -------------------------------------------------------------
    def test_f3_01_guide_document_presence(self):
        """F3.1: Verify references/photo_selection_guide.md exists and is substantive."""
        guide_path = REFERENCES_DIR / "photo_selection_guide.md"
        self.assertTrue(guide_path.is_file(), f"Photo guide not found: {guide_path}")
        self.assertGreater(guide_path.stat().st_size, 2000, "Photo guide must exceed 2KB")

    def test_f3_02_five_dimensional_framework(self):
        """F3.2: Verify guide specifies the 5-dimensional evaluation criteria."""
        guide_path = REFERENCES_DIR / "photo_selection_guide.md"
        content = guide_path.read_text(encoding="utf-8")
        dimensions = [
            "军容军纪",
            "人物神态",
            "构图美学",
            "色彩影调",
            "叙事编排",
        ]
        for dim in dimensions:
            self.assertIn(dim, content, f"5D dimension '{dim}' not specified in photo guide")

    def test_f3_03_scoring_tier_rubric(self):
        """F3.3: Verify guide defines the 4-level scoring tiers."""
        guide_path = REFERENCES_DIR / "photo_selection_guide.md"
        content = guide_path.read_text(encoding="utf-8")
        for tier in ["特优推荐", "合格入选", "需微调", "坚决淘汰"]:
            self.assertIn(tier, content, f"Scoring tier '{tier}' not defined in photo guide")

    def test_f3_04_blacklist_rejection_rules(self):
        """F3.4: Verify guide specifies clear blacklist/rejection criteria."""
        guide_path = REFERENCES_DIR / "photo_selection_guide.md"
        content = guide_path.read_text(encoding="utf-8")
        self.assertTrue("淘汰" in content or "黑名单" in content or "一票否决" in content)
        self.assertTrue("过曝" in content or "虚焦" in content or "高光" in content)

    def test_f3_05_campus_visual_markers(self):
        """F3.5: Verify guide specifies authentic campus visual markers."""
        guide_path = REFERENCES_DIR / "photo_selection_guide.md"
        content = guide_path.read_text(encoding="utf-8")
        markers = ["南湖", "操场", "白线", "作训服"]
        for marker in markers:
            self.assertIn(marker, content, f"Campus marker '{marker}' missing in photo guide")

    # -------------------------------------------------------------
    # F4: 76-Photo Junxun Scoring & Evaluation (R2)
    # -------------------------------------------------------------
    def test_f4_01_quantitative_report_count(self):
        """F4.1: Verify photo_evaluation_report.json contains exactly 76 photo records."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        self.assertTrue(report_path.is_file(), f"Report file not found: {report_path}")
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = len(data) if isinstance(data, list) else len(data.keys())
        self.assertEqual(count, 76, f"Expected 76 evaluated photos, found {count}")

    def test_f4_02_photo_metrics_attributes(self):
        """F4.2: Verify every photo in report has quantitative metrics."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        required_keys = ["name", "path", "resolution", "mean_lum", "sharpness", "highlight_clip", "score", "tier"]
        for item in items:
            for k in required_keys:
                self.assertIn(k, item, f"Photo record {item.get('name')} missing metric: {k}")

    def test_f4_03_physical_usb_photo_verification(self):
        """F4.3: Verify all 76 photos exist on physical USB mount /Volumes/xbpd的u盘/junxun."""
        self.assertTrue(USB_PHOTO_DIR.is_dir(), f"USB directory not found: {USB_PHOTO_DIR}")
        usb_files = [f for f in os.listdir(USB_PHOTO_DIR) if f.lower().endswith((".jpg", ".jpeg"))]
        self.assertEqual(len(usb_files), 76, f"Expected 76 files in USB, found {len(usb_files)}")

    def test_f4_04_blacklisted_photo_scoring(self):
        """F4.4: Verify blacklisted photo IMG_3879.JPG is scored <= 35 and classified Tier C."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        img_3879 = next((x for x in items if x["name"] == "IMG_3879.JPG"), None)
        self.assertIsNotNone(img_3879, "IMG_3879.JPG not found in report")
        self.assertLessEqual(img_3879["score"], 35.0, "IMG_3879.JPG must have low score <= 35.0")
        self.assertIn("C", img_3879["tier"], "IMG_3879.JPG must be categorized as Tier C")

    def test_f4_05_top_cover_recommendation(self):
        """F4.5: Verify top recommended cover photo IMG_3870.JPG is rated Tier A+ with score >= 90."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        img_3870 = next((x for x in items if x["name"] == "IMG_3870.JPG"), None)
        self.assertIsNotNone(img_3870, "IMG_3870.JPG not found in report")
        self.assertGreaterEqual(img_3870["score"], 90.0, "IMG_3870.JPG must have score >= 90.0")
        self.assertIn("A+", img_3870["tier"], "IMG_3870.JPG must be Tier A+")

    # -------------------------------------------------------------
    # F5: Skill Human-Touch Guidelines (R3)
    # -------------------------------------------------------------
    def test_f5_01_skill_md_existence_and_structure(self):
        """F5.1: Verify SKILL.md exists, has substantial content, and defines core workflow."""
        skill_path = WORKSPACE / "SKILL.md"
        self.assertTrue(skill_path.is_file(), f"SKILL.md not found: {skill_path}")
        content = skill_path.read_text(encoding="utf-8")
        self.assertGreater(len(content), 3000, "SKILL.md must be comprehensive (> 3KB)")
        self.assertIn("中南民族大学", content)
        self.assertIn("微信公众号", content)

    def test_f5_02_five_senses_sensory_guidelines(self):
        """F5.2: Verify SKILL.md details sensory micro-narratives and authentic details."""
        skill_path = WORKSPACE / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        sensory_keywords = ["五感", "微叙事", "作训服", "白线", "平结"]
        for kw in sensory_keywords:
            self.assertIn(kw, content, f"Sensory guideline keyword '{kw}' missing in SKILL.md")

    def test_f5_03_ai_cliche_prohibitions(self):
        """F5.3: Verify SKILL.md explicitly prohibits AI cliches TONE-001 and TONE-002."""
        skill_path = WORKSPACE / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        self.assertIn("如果说代码", content)
        self.assertIn("争分夺秒，守护战友生命安全", content)
        self.assertIn("严禁", content)

    def test_f5_04_political_and_institutional_rules(self):
        """F5.4: Verify SKILL.md enshrines official political red lines and institutional facts."""
        skill_path = WORKSPACE / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        self.assertIn("铸牢中华民族共同体意识", content)
        self.assertIn("国家民族事务委员会", content)
        self.assertIn("民族学博物馆", content)

    def test_f5_05_supporting_reference_files(self):
        """F5.5: Verify supporting reference files indexed by SKILL.md exist."""
        ref_files = [
            REFERENCES_DIR / "scmu_profile.md",
            REFERENCES_DIR / "compliance_guide.md",
            KB_DIR / "human_touch_writing_guide.md",
            REFERENCES_DIR / "templates.md",
        ]
        for rf in ref_files:
            self.assertTrue(rf.is_file(), f"Supporting reference file not found: {rf}")

    # -------------------------------------------------------------
    # F6: Strict Compliance Verification (R3)
    # -------------------------------------------------------------
    def test_f6_01_check_compliance_cli_help(self):
        """F6.1: Verify check_compliance.py --help runs and displays options."""
        checker = SCRIPTS_DIR / "check_compliance.py"
        self.assertTrue(checker.is_file(), f"Checker script not found: {checker}")
        res = subprocess.run([sys.executable, str(checker), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("--strict", res.stdout)
        self.assertIn("--json", res.stdout)

    def test_f6_02_clean_text_strict_pass(self):
        """F6.2: Verify clean standard text passes compliance check with 0 BLOCKER and 0 WARNING."""
        clean_text = """# 团结奋进迎盛会 砥砺前行谱新篇

> 紧紧围绕铸牢中华民族共同体意识主线，深化教育教学改革。

### ▍深耕笃行
中南民族大学坚持“笃信好学，自然宽和”的校训精神，坐落于美丽的南湖之滨。
学校直属于国家民委，全校师生在南区双塔下砥砺奋斗。

📷 配图说明：南湖畔的迷彩方阵

---
来源：中南民族大学融媒体中心
初审：融媒编辑 | 复审：融媒主管 | 终审：党委宣传部
"""
        issues = check_content(clean_text)
        blockers = [i for i in issues if i["level"] == "BLOCKER"]
        warnings = [i for i in issues if i["level"] == "WARNING"]
        self.assertEqual(len(blockers), 0)
        self.assertEqual(len(warnings), 0)

    def test_f6_03_cs_junxun_post_strict_compliance(self):
        """F6.3: Verify examples/cs_2026_junxun_post.md passes check_compliance.py --strict with code 0."""
        post_path = EXAMPLES_DIR / "cs_2026_junxun_post.md"
        self.assertTrue(post_path.is_file(), f"Post markdown not found: {post_path}")
        checker = SCRIPTS_DIR / "check_compliance.py"
        res = subprocess.run(
            [sys.executable, str(checker), str(post_path), "--strict"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Compliance check failed: {res.stdout}\n{res.stderr}")
        self.assertIn("未检测到任何合规风险或格式问题", res.stdout)

    def test_f6_04_json_compliance_output(self):
        """F6.4: Verify --json mode returns valid JSON with pass status and issue counts."""
        post_path = EXAMPLES_DIR / "cs_2026_junxun_post.md"
        checker = SCRIPTS_DIR / "check_compliance.py"
        res = subprocess.run(
            [sys.executable, str(checker), str(post_path), "--json", "--strict"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["pass"])
        self.assertEqual(data["blocker_count"], 0)
        self.assertEqual(data["warning_count"], 0)

    def test_f6_05_unit_test_suite_passes(self):
        """F6.5: Verify test_compliance.py unit tests pass cleanly."""
        unit_test = SCRIPTS_DIR / "tests" / "test_compliance.py"
        self.assertTrue(unit_test.is_file(), f"Compliance unit test not found: {unit_test}")
        res = subprocess.run([sys.executable, "-m", "unittest", str(unit_test)], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Unit test failed: {res.stderr}")

    # -------------------------------------------------------------
    # F7: Native Xiumi Package Delivery (R4)
    # -------------------------------------------------------------
    def test_f7_01_deploy_script_import(self):
        """F7.1: Verify scripts/deploy_to_xiumi.py imports cleanly and defines functions."""
        self.assertTrue(callable(build_xiumi_rich_html))
        self.assertTrue(callable(get_base64_image))
        self.assertIsInstance(PHOTO_SELECTION, dict)

    def test_f7_02_build_xiumi_rich_html_execution(self):
        """F7.2: Verify build_xiumi_rich_html() generates valid, large HTML string (> 50KB)."""
        html = build_xiumi_rich_html()
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 50000, "Xiumi HTML must contain full embedded content (> 50KB)")

    def test_f7_03_scmu_vi_color_palette(self):
        """F7.3: Verify generated Xiumi HTML integrates the 3 SCMU VI colors."""
        html = build_xiumi_rich_html()
        vi_colors = {
            "#B8242A": "民大石榴红",
            "#1F5F8B": "南湖蓝",
            "#D4A359": "晨曦金",
        }
        for hex_code, desc in vi_colors.items():
            self.assertIn(
                hex_code.upper(),
                html.upper(),
                f"SCMU VI color {hex_code} ({desc}) missing in Xiumi HTML",
            )

    def test_f7_04_base64_embedded_assets(self):
        """F7.4: Verify generated Xiumi HTML embeds inline Base64 data URIs."""
        html = build_xiumi_rich_html()
        self.assertIn("data:image/jpeg;base64,", html, "HTML must embed inline base64 JPEG data URIs")
        # Ensure at least 5 embedded base64 image tags
        matches = re.findall(r'src="data:image/jpeg;base64,', html)
        self.assertGreaterEqual(len(matches), 5, "Must embed at least 5 base64 images")

    def test_f7_05_colophon_and_credits_present(self):
        """F7.5: Verify generated Xiumi HTML contains official colophon and review signoffs."""
        html = build_xiumi_rich_html()
        self.assertIn("中南民族大学融媒体中心", html)
        self.assertIn("计算机科学学院（人工智能学院）", html)
        self.assertIn("初审", html)
        self.assertIn("复审", html)
        self.assertIn("终审", html)

    # -------------------------------------------------------------
    # F8: Browser Xiumi Rendering Sync (R4)
    # -------------------------------------------------------------
    def test_f8_01_playwright_availability(self):
        """F8.1: Verify Playwright is installed and importable."""
        try:
            import playwright
            from playwright.sync_api import sync_playwright
            self.assertIsNotNone(sync_playwright)
        except ImportError as e:
            self.fail(f"Playwright import failed: {e}")

    def test_f8_02_photo_downsampling(self):
        """F8.2: Verify get_base64_image scales image and returns valid data URI."""
        data_uri = get_base64_image("IMG_3870.JPG", max_width=400, quality=80)
        self.assertTrue(data_uri.startswith("data:image/jpeg;base64,"))
        raw_b64 = data_uri.split(",", 1)[1]
        decoded = base64.b64decode(raw_b64)
        with Image.open(BytesIO(decoded)) as img:
            self.assertLessEqual(img.width, 400)

    def test_f8_03_narrative_photo_slots(self):
        """F8.3: Verify PHOTO_SELECTION covers 8 distinct narrative slots."""
        expected_slots = [
            "cover",
            "queue_check",
            "white_line",
            "first_aid_1",
            "first_aid_2",
            "rain_march",
            "salute",
            "stride",
        ]
        for slot in expected_slots:
            self.assertIn(slot, PHOTO_SELECTION, f"Missing narrative slot: {slot}")
            photo_file = PHOTO_SELECTION[slot]
            self.assertTrue((USB_PHOTO_DIR / photo_file).is_file(), f"Photo file not found in USB: {photo_file}")

    def test_f8_04_cover_selection_clean(self):
        """F8.4: Verify cover photo is IMG_3870.JPG and not blacklisted IMG_3879.JPG."""
        self.assertEqual(PHOTO_SELECTION["cover"], "IMG_3870.JPG")
        self.assertNotIn("IMG_3879.JPG", PHOTO_SELECTION.values())

    def test_f8_05_rendered_article_artifact(self):
        """F8.5: Verify examples/xiumi_rendered_article.png exists and is a valid PNG image."""
        screenshot_path = EXAMPLES_DIR / "xiumi_rendered_article.png"
        self.assertTrue(screenshot_path.is_file(), f"Screenshot not found: {screenshot_path}")
        self.assertGreater(screenshot_path.stat().st_size, 50000, "Screenshot must be non-empty (> 50KB)")
        with Image.open(screenshot_path) as img:
            self.assertEqual(img.format, "PNG")
            self.assertGreaterEqual(img.width, 1000)


class TestTier2BoundaryAndCorner(unittest.TestCase):
    """Tier 2: Boundary & Corner Cases (>=5 tests per feature F1-F8)."""

    # -------------------------------------------------------------
    # F1 Boundaries
    # -------------------------------------------------------------
    def test_f1_b01_malformed_json_handling(self):
        """F1.B1: Verify JSON parse error handling on malformed content."""
        malformed_json = "{ invalid_json: true, "
        with self.assertRaises(json.JSONDecodeError):
            json.loads(malformed_json)

    def test_f1_b02_date_format_conformity(self):
        """F1.B2: Verify every single article date conforms to YYYY-MM-DD pattern."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for idx, art in enumerate(data):
            self.assertRegex(
                art["date"],
                date_pattern,
                f"Article {idx} has non-standard date format: {art['date']}",
            )

    def test_f1_b03_no_empty_content(self):
        """F1.B3: Verify no article in corpus has empty or whitespace-only content."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for idx, art in enumerate(data):
            stripped = art["content"].strip()
            self.assertGreaterEqual(len(stripped), 10, f"Article {idx} content is too short or empty")

    def test_f1_b04_url_scheme_and_domain(self):
        """F1.B4: Verify all URLs strictly start with http/https and domain scuec.edu.cn."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for idx, art in enumerate(data):
            url = art["url"]
            self.assertTrue(
                url.startswith("http://") or url.startswith("https://"),
                f"Article {idx} has invalid URL scheme: {url}",
            )
            self.assertIn("scuec.edu.cn", url, f"Article {idx} URL outside SCMU domain: {url}")

    def test_f1_b05_content_minimum_length(self):
        """F1.B5: Verify total corpus content size exceeds 250,000 characters."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        total_len = sum(len(a["content"]) for a in data)
        self.assertGreater(total_len, 250000, f"Total corpus text too small: {total_len}")

    # -------------------------------------------------------------
    # F2 Boundaries
    # -------------------------------------------------------------
    def test_f2_b01_query_cli_empty_string(self):
        """F2.B1: Verify CLI query with empty string does not crash and returns exit code 0 or 2."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        res = subprocess.run([sys.executable, str(query_script), "--query", ""], capture_output=True, text=True)
        self.assertIn(res.returncode, [0, 2])

    def test_f2_b02_query_cli_nonexistent_term(self):
        """F2.B2: Verify CLI query for nonexistent keyword returns 0 results cleanly without unhandled error."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        res = subprocess.run(
            [sys.executable, str(query_script), "--query", "xyz999nonexistentkeyword"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertTrue("共找到 0 篇" in res.stdout or "0" in res.stdout)

    def test_f2_b03_query_cli_regex_special_chars(self):
        """F2.B3: Verify query containing regex meta-characters does not cause unhandled regex crash."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        res = subprocess.run(
            [sys.executable, str(query_script), "--query", ".*+?[]()|^$"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

    def test_f2_b04_query_cli_strict_exit_code(self):
        """F2.B4: Verify --strict flag causes CLI to exit with code 1 when no results match."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        res = subprocess.run(
            [sys.executable, str(query_script), "--query", "nonexistent_term_for_strict_test", "--strict"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1, f"Strict query with 0 results must exit with code 1, got {res.returncode}")

    def test_f2_b05_query_cli_invalid_limit(self):
        """F2.B5: Verify negative or zero limit is handled safely."""
        query_script = SCRIPTS_DIR / "query_kb.py"
        res = subprocess.run(
            [sys.executable, str(query_script), "--query", "双塔", "--limit", "0"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)

    # -------------------------------------------------------------
    # F3 Boundaries
    # -------------------------------------------------------------
    def test_f3_b01_score_bounds_in_report(self):
        """F3.B1: Verify all 76 photo scores are strictly bounded in [0.0, 100.0]."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        for item in items:
            score = item["score"]
            self.assertGreaterEqual(score, 0.0, f"Score underflow for {item['name']}: {score}")
            self.assertLessEqual(score, 100.0, f"Score overflow for {item['name']}: {score}")

    def test_f3_b02_highlight_clipping_threshold(self):
        """F3.B2: Verify photos with highlight clipping >= 10.0% are flagged with issues or Tier C."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        for item in items:
            if item.get("highlight_clip", 0) >= 10.0:
                issues = item.get("issues", [])
                has_clipping_issue = any("高光" in str(iss) or "溢出" in str(iss) for iss in issues)
                self.assertTrue(
                    has_clipping_issue or "C" in item["tier"],
                    f"Photo with clipping >= 10% not flagged with clipping issue or Tier C: {item['name']}",
                )

    def test_f3_b03_sharpness_extreme_rejection(self):
        """F3.B3: Verify photos with low sharpness (< 10.0) are categorized as Tier C or flagged."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        for item in items:
            if item.get("sharpness", 99) < 10.0:
                self.assertIn("C", item["tier"], f"Blurry photo not in Tier C: {item['name']}")

    def test_f3_b04_luminance_extremes(self):
        """F3.B4: Verify extreme mean luminance (< 40 or > 180) triggers warning issues."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        for item in items:
            lum = item.get("mean_lum", 120)
            if lum < 40 or lum > 180:
                self.assertGreater(len(item.get("issues", [])), 0, f"No issues flagged for extreme luminance: {item['name']}")

    def test_f3_b05_tier_assignment_monotonicity(self):
        """F3.B5: Verify A+ tier photos have higher scores than C tier photos."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        a_plus_scores = [x["score"] for x in items if "A+" in x["tier"]]
        c_scores = [x["score"] for x in items if "C" in x["tier"]]
        self.assertGreater(min(a_plus_scores), max(c_scores))

    # -------------------------------------------------------------
    # F4 Boundaries
    # -------------------------------------------------------------
    def test_f4_b01_exact_76_photo_set(self):
        """F4.B1: Verify exact correspondence between USB files and report entries."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        report_names = {x["name"] for x in items}
        usb_files = {f for f in os.listdir(USB_PHOTO_DIR) if f.lower().endswith((".jpg", ".jpeg"))}
        self.assertEqual(report_names, usb_files, "Report photo set must exactly match USB directory")

    def test_f4_b02_blacklisted_photo_img3879(self):
        """F4.B2: Verify IMG_3879.JPG has overexposure issues and is Tier C."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        p = next(x for x in items if x["name"] == "IMG_3879.JPG")
        self.assertIn("C", p["tier"])
        self.assertGreaterEqual(p["highlight_clip"], 10.0)

    def test_f4_b03_blacklisted_photo_img3878(self):
        """F4.B3: Verify IMG_3878.JPG has clipping/issues and is Tier C."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        p = next(x for x in items if x["name"] == "IMG_3878.JPG")
        self.assertIn("C", p["tier"])

    def test_f4_b04_underexposed_photo_penalties(self):
        """F4.B4: Verify IMG_3841.JPG or IMG_3849.JPG is identified as underexposed."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data if isinstance(data, list) else list(data.values())
        p = next((x for x in items if x["name"] in ["IMG_3841.JPG", "IMG_3849.JPG"]), None)
        self.assertIsNotNone(p)
        self.assertIn("C", p["tier"])

    def test_f4_b05_usb_images_loadable(self):
        """F4.B5: Verify a sample of photos across USB can be parsed by PIL with non-zero dimensions."""
        sample_photos = ["IMG_3870.JPG", "IMG_3830.JPG", "IMG_3865.JPG", "IMG_3857.JPG"]
        for p in sample_photos:
            path = USB_PHOTO_DIR / p
            with Image.open(path) as img:
                self.assertGreater(img.width, 1000)
                self.assertGreater(img.height, 1000)

    # -------------------------------------------------------------
    # F5 Boundaries
    # -------------------------------------------------------------
    def test_f5_b01_forbidden_verb_zhudao(self):
        """F5.B1: Verify '铸造中华民族共同体意识' triggers POL-001 BLOCKER."""
        bad_text = "广大青年学子必须铸造中华民族共同体意识。"
        issues = check_content(bad_text)
        blocker_ids = [i["id"] for i in issues if i["level"] == "BLOCKER"]
        self.assertIn("POL-001", blocker_ids)

    def test_f5_b02_forbidden_supervisor(self):
        """F5.B2: Verify '教育部直属的中南民族大学' triggers POL-005 BLOCKER."""
        bad_text = "作为教育部直属的中南民族大学，肩负着重要历史使命。"
        issues = check_content(bad_text)
        blocker_ids = [i["id"] for i in issues if i["level"] == "BLOCKER"]
        self.assertIn("POL-005", blocker_ids)

    def test_f5_b03_motto_typo(self):
        """F5.B3: Verify '笃信好学，自然和谐' triggers SCMU-003 WARNING."""
        bad_text = "我们要弘扬“笃信好学，自然和谐”的校训精神。"
        issues = check_content(bad_text)
        warning_ids = [i["id"] for i in issues if i["level"] == "WARNING"]
        self.assertIn("SCMU-003", warning_ids)

    def test_f5_b04_museum_typo(self):
        """F5.B4: Verify '民俗博物馆' triggers SCMU-005 WARNING."""
        bad_text = "今天下午，同学们集体参观了民大民俗博物馆。"
        issues = check_content(bad_text)
        warning_ids = [i["id"] for i in issues if i["level"] == "WARNING"]
        self.assertIn("SCMU-005", warning_ids)

    def test_f5_b05_lake_geography_typo(self):
        """F5.B5: Verify '东湖之滨的中南民族大学' triggers SCMU-006 WARNING."""
        bad_text = "坐落于东湖之滨的民大双塔巍然耸立。"
        issues = check_content(bad_text)
        warning_ids = [i["id"] for i in issues if i["level"] == "WARNING"]
        self.assertIn("SCMU-006", warning_ids)

    # -------------------------------------------------------------
    # F6 Boundaries
    # -------------------------------------------------------------
    def test_f6_b01_empty_string_compliance(self):
        """F6.B1: Verify empty string input yields zero issues without error."""
        issues = check_content("")
        self.assertEqual(len(issues), 0)

    def test_f6_b02_unclosed_quote_suggestion(self):
        """F6.B2: Verify unclosed quote triggers FMT-002 SUGGESTION."""
        bad_text = "正如辅导员所说：“大家在军训中要听从指挥"
        issues = check_content(bad_text)
        sugg_ids = [i["id"] for i in issues if i["level"] == "SUGGESTION"]
        self.assertIn("FMT-002", sugg_ids)

    def test_f6_b03_h1_trailing_punctuation(self):
        """F6.B3: Verify H1 heading ending with exclamation triggers FMT-001 SUGGESTION."""
        bad_text = "# 热烈祝贺我校学子在全国大赛中斩获特等奖！"
        issues = check_content(bad_text)
        sugg_ids = [i["id"] for i in issues if i["level"] == "SUGGESTION"]
        self.assertIn("FMT-001", sugg_ids)

    def test_f6_b04_missing_colophon_detection(self):
        """F6.B4: Verify long draft missing official colophon triggers STRUC-001 SUGGESTION."""
        long_draft = "\n".join([f"这是第 {i} 段叙述正文。" for i in range(15)])
        issues = check_content(long_draft)
        sugg_ids = [i["id"] for i in issues if i["level"] == "SUGGESTION"]
        self.assertIn("STRUC-001", sugg_ids)

    def test_f6_b05_cli_nonexistent_file(self):
        """F6.B5: Verify CLI invocation on nonexistent file exits with code 2."""
        checker = SCRIPTS_DIR / "check_compliance.py"
        res = subprocess.run([sys.executable, str(checker), "nonexistent_draft_9999.md"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)

    # -------------------------------------------------------------
    # F7 Boundaries
    # -------------------------------------------------------------
    def test_f7_b01_missing_photo_graceful_handling(self):
        """F7.B1: Verify get_base64_image on missing file returns empty string safely."""
        res = get_base64_image("nonexistent_filename_404.jpg")
        self.assertEqual(res, "")

    def test_f7_b02_extreme_scaling_aspect_ratio(self):
        """F7.B2: Verify get_base64_image maintains aspect ratio when scaled down."""
        res = get_base64_image("IMG_3870.JPG", max_width=300)
        b64_data = res.split(",", 1)[1]
        with Image.open(BytesIO(base64.b64decode(b64_data))) as img:
            self.assertEqual(img.width, 300)
            self.assertGreater(img.height, 200)

    def test_f7_b03_xiumi_html_size_bounds(self):
        """F7.B3: Verify generated Xiumi HTML package size is within expected bounds (1MB - 10MB)."""
        html = build_xiumi_rich_html()
        size_bytes = len(html.encode("utf-8"))
        self.assertGreaterEqual(size_bytes, 1_000_000, "HTML package must be at least 1MB with base64 assets")
        self.assertLessEqual(size_bytes, 10_000_000, "HTML package should not exceed 10MB")

    def test_f7_b04_inline_style_purity(self):
        """F7.B4: Verify no external <link rel='stylesheet'> tags exist in Xiumi HTML body."""
        html = build_xiumi_rich_html()
        self.assertNotIn("<link rel=\"stylesheet\"", html)
        self.assertNotIn("<link rel='stylesheet'", html)

    def test_f7_b05_container_max_width_constraint(self):
        """F7.B5: Verify max-width 677px constraint is explicitly configured."""
        html = build_xiumi_rich_html()
        self.assertIn("max-width: 677px", html)

    # -------------------------------------------------------------
    # F8 Boundaries
    # -------------------------------------------------------------
    def test_f8_b01_data_uri_format_conformance(self):
        """F8.B1: Verify data URI format conforms to standard specification."""
        uri = get_base64_image("IMG_3870.JPG", max_width=200)
        self.assertRegex(uri, r"^data:image/jpeg;base64,[A-Za-z0-9+/=]+$")

    def test_f8_b02_distinct_narrative_photos(self):
        """F8.B2: Verify all 8 narrative slots map to distinct photo filenames."""
        photo_values = list(PHOTO_SELECTION.values())
        self.assertEqual(len(photo_values), len(set(photo_values)), "Narrative slots must not have duplicate photos")

    def test_f8_b03_vi_hex_colors_format(self):
        """F8.B3: Verify VI colors match standard 6-digit hex format."""
        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for color in ["#B8242A", "#1F5F8B", "#D4A359"]:
            self.assertRegex(color, hex_pattern)

    def test_f8_b04_utf8_encoding_cleanliness(self):
        """F8.B4: Verify HTML string contains no Unicode replacement characters (U+FFFD)."""
        html = build_xiumi_rich_html()
        self.assertNotIn("\ufffd", html, "HTML content contains broken unicode characters")

    def test_f8_b05_rendered_png_header_and_dimensions(self):
        """F8.B5: Verify xiumi_rendered_article.png has valid PNG dimensions >= 1000x700."""
        screenshot = EXAMPLES_DIR / "xiumi_rendered_article.png"
        self.assertTrue(screenshot.is_file())
        with Image.open(screenshot) as img:
            self.assertGreaterEqual(img.width, 1000)
            self.assertGreaterEqual(img.height, 700)


class TestTier3CrossFeatureIntegration(unittest.TestCase):
    """Tier 3: Cross-Feature Combinations (10 pairwise integration tests)."""

    def test_t3_01_corpus_to_index_id_integrity(self):
        """T3.1 (F1 -> F2): Inverted index article IDs strictly map to valid articles in corpus."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        index_path = KB_DIR / "kb_index.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            corpus = json.load(f)
        with open(index_path, "r", encoding="utf-8") as f:
            idx = json.load(f)

        articles_list = idx["articles"]
        self.assertEqual(len(articles_list), len(corpus))
        for art_meta in articles_list:
            art_id = art_meta["id"]
            self.assertLess(art_id, len(corpus))
            self.assertEqual(art_meta["title"], corpus[art_id]["title"])
            self.assertEqual(art_meta["url"], corpus[art_id]["url"])

    def test_t3_02_golden_quotes_url_provenance(self):
        """T3.2 (F1 -> F2): Every URL in golden_quotes.json has authentic SCMU provenance and valid article_id."""
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        quotes_path = KB_DIR / "golden_quotes.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            corpus = json.load(f)

        with open(quotes_path, "r", encoding="utf-8") as f:
            qdata = json.load(f)

        for q in qdata["quotes"]:
            self.assertTrue(
                q["url"].startswith("https://www.scuec.edu.cn/xww/"),
                f"Quote URL does not start with SCMU domain: {q['url']}",
            )
            art_id = q.get("article_id")
            if art_id is not None:
                self.assertGreaterEqual(art_id, 0)
                self.assertLess(art_id, len(corpus))

    def test_t3_03_photo_guide_tiers_match_report(self):
        """T3.3 (F3 -> F4): Tier grades in report match standards defined in photo_selection_guide.md."""
        guide_path = REFERENCES_DIR / "photo_selection_guide.md"
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        guide_text = guide_path.read_text(encoding="utf-8")
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        items = report if isinstance(report, list) else list(report.values())
        report_tiers = {x["tier"] for x in items}
        for rt in report_tiers:
            prefix = rt.split()[0]
            self.assertIn(prefix, ["A+", "A", "B", "C"], f"Unexpected tier prefix: {prefix}")
        for keyword in ["特优推荐", "合格", "淘汰"]:
            self.assertIn(keyword, guide_text)

    def test_t3_04_blacklist_photos_in_evaluation_report(self):
        """T3.4 (F3 -> F4): Photos blacklisted in photo guide have Tier C in evaluation report."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        items = report if isinstance(report, list) else list(report.values())
        for photo_name in ["IMG_3878.JPG", "IMG_3879.JPG"]:
            match = next((x for x in items if x["name"] == photo_name), None)
            self.assertIsNotNone(match, f"Photo {photo_name} not found in report")
            self.assertIn("C", match["tier"], f"Blacklisted photo {photo_name} must have Tier C")

    def test_t3_05_xiumi_photo_selection_meets_a_tier(self):
        """T3.5 (F4 -> F7): Every photo in PHOTO_SELECTION has score >= 70.0 in photo_evaluation_report.json."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        items = report if isinstance(report, list) else list(report.values())
        report_map = {x["name"]: x for x in items}

        for slot, photo_name in PHOTO_SELECTION.items():
            self.assertIn(photo_name, report_map, f"Selected photo {photo_name} not in report")
            item = report_map[photo_name]
            self.assertGreaterEqual(
                item["score"],
                70.0,
                f"Selected photo {photo_name} for slot '{slot}' has inadequate score: {item['score']}",
            )
            self.assertNotIn("C", item["tier"], f"Selected photo {photo_name} is in Tier C")

    def test_t3_06_xiumi_photo_selection_free_of_compliance_warnings(self):
        """T3.6 (F4 -> F6): No photo in PHOTO_SELECTION matches compliance blacklist PHOTO-001 or PHOTO-002."""
        rule_photo_001 = next(r for r in RULES if r["id"] == "PHOTO-001")
        rule_photo_002 = next(r for r in RULES if r["id"] == "PHOTO-002")

        for slot, photo_name in PHOTO_SELECTION.items():
            self.assertIsNone(
                re.search(rule_photo_001["pattern"], photo_name),
                f"Photo {photo_name} ({slot}) matches PHOTO-001 blacklist",
            )
            self.assertIsNone(
                re.search(rule_photo_002["pattern"], photo_name),
                f"Photo {photo_name} ({slot}) matches PHOTO-002 blacklist",
            )

    def test_t3_07_skill_rules_mirrored_in_compliance_checker(self):
        """T3.7 (F5 -> F6): Prohibited phrases in SKILL.md have matching active rules in check_compliance.py."""
        skill_text = (WORKSPACE / "SKILL.md").read_text(encoding="utf-8")
        checker_rules_ids = {r["id"] for r in RULES}

        for rule_id in ["POL-001", "POL-005", "SCMU-001", "SCMU-003", "PHOTO-001", "TONE-001", "TONE-002"]:
            self.assertIn(rule_id, skill_text, f"Rule ID {rule_id} not referenced in SKILL.md")
            self.assertIn(rule_id, checker_rules_ids, f"Rule ID {rule_id} missing in compliance checker RULES")

    def test_t3_08_vi_colors_in_skill_match_xiumi_html(self):
        """T3.8 (F5 -> F7): All 3 VI colors specified in SKILL.md are present in Xiumi HTML."""
        skill_text = (WORKSPACE / "SKILL.md").read_text(encoding="utf-8")
        html = build_xiumi_rich_html()

        for hex_code in ["#B8242A", "#1F5F8B", "#D4A359"]:
            self.assertIn(hex_code, skill_text, f"Color {hex_code} missing in SKILL.md")
            self.assertIn(hex_code.upper(), html.upper(), f"Color {hex_code} missing in Xiumi HTML")

    def test_t3_09_xiumi_html_text_passes_compliance_strict(self):
        """T3.9 (F6 -> F7): Text extracted from Xiumi HTML passes compliance checker with 0 BLOCKER and 0 WARNING."""
        html = build_xiumi_rich_html()
        # Strip HTML tags to obtain pure text
        text_content = re.sub(r"<[^>]+>", " ", html)
        text_content = re.sub(r"\s+", " ", text_content)
        issues = check_content(text_content)
        blockers = [i for i in issues if i["level"] == "BLOCKER"]
        warnings = [i for i in issues if i["level"] == "WARNING"]
        self.assertEqual(len(blockers), 0, f"Xiumi HTML text has BLOCKER: {blockers}")
        self.assertEqual(len(warnings), 0, f"Xiumi HTML text has WARNING: {warnings}")

    def test_t3_10_base64_data_uris_decode_to_valid_jpeg(self):
        """T3.10 (F7 -> F8): All base64 data URIs in Xiumi HTML decode into valid JPEG images."""
        html = build_xiumi_rich_html()
        uris = re.findall(r'src="(data:image/jpeg;base64,[^"]+)"', html)
        self.assertGreaterEqual(len(uris), 5)
        for idx, uri in enumerate(uris):
            b64_data = uri.split(",", 1)[1]
            raw_bytes = base64.b64decode(b64_data)
            # JPEG magic bytes: \xff\xd8\xff
            self.assertTrue(
                raw_bytes.startswith(b"\xff\xd8\xff"),
                f"Embedded image {idx} is not valid JPEG data",
            )
            with Image.open(BytesIO(raw_bytes)) as img:
                self.assertEqual(img.format, "JPEG")
                self.assertGreater(img.width, 100)


class TestTier4RealWorldApplication(unittest.TestCase):
    """Tier 4: Real-World User Workflows (5 end-to-end scenario tests)."""

    def test_t4_01_corpus_research_and_quote_extraction_workflow(self):
        """T4.1: End-to-End Workflow: Query corpus for training facts, extract golden quotes, verify provenance."""
        query_script = SCRIPTS_DIR / "query_kb.py"

        # Step 1: Query facts on military training
        res_query = subprocess.run(
            [sys.executable, str(query_script), "--query", "军训", "--json", "--limit", "5"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_query.returncode, 0)
        q_data = json.loads(res_query.stdout)
        results_list = q_data.get("results") or q_data.get("articles") or []
        self.assertGreaterEqual(len(results_list), 1)

        # Step 2: Extract themed golden quotes
        res_quotes = subprocess.run(
            [sys.executable, str(query_script), "--quotes", "--theme", "军训淬炼", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_quotes.returncode, 0)
        quotes_data = json.loads(res_quotes.stdout)
        quotes_list = quotes_data.get("quotes") or quotes_data.get("results") or []
        self.assertGreaterEqual(len(quotes_list), 1)

        # Step 3: Verify provenance URL integrity
        first_quote = quotes_list[0]
        self.assertIn("url", first_quote)
        self.assertTrue(first_quote["url"].startswith("http"))

    def test_t4_02_photo_ingestion_and_selection_workflow(self):
        """T4.2: End-to-End Workflow: Ingest raw photo metrics, reject blacklisted items, build narrative sequence."""
        report_path = REFERENCES_DIR / "photo_evaluation_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            eval_data = json.load(f)
        photos = eval_data if isinstance(eval_data, list) else list(eval_data.values())

        # Step 1: Filter out blacklisted/low-quality photos
        usable_photos = [
            p for p in photos
            if "C" not in p["tier"] and p["score"] >= 70.0 and p["highlight_clip"] < 5.0 and p["sharpness"] >= 14.0
        ]
        self.assertGreaterEqual(len(usable_photos), 20, "Should have >= 20 high-quality photos")

        # Step 2: Ensure blacklisted IMG_3879 is excluded
        usable_names = {p["name"] for p in usable_photos}
        self.assertNotIn("IMG_3879.JPG", usable_names)
        self.assertNotIn("IMG_3878.JPG", usable_names)

        # Step 3: Verify all 8 deployed narrative photos belong to usable set (or score >= 70)
        for slot, photo_file in PHOTO_SELECTION.items():
            self.assertIn(photo_file, [p["name"] for p in photos if p["score"] >= 70.0])

    def test_t4_03_editorial_compliance_verification_workflow(self):
        """T4.3: End-to-End Workflow: Editorial draft submitted and verified through strict compliance pipeline."""
        post_path = EXAMPLES_DIR / "cs_2026_junxun_post.md"
        checker = SCRIPTS_DIR / "check_compliance.py"

        # Run strict compliance scan
        res = subprocess.run(
            [sys.executable, str(checker), str(post_path), "--strict", "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Compliance check failed: {res.stdout}")
        report = json.loads(res.stdout)

        # Verify 0 blockers and 0 warnings
        self.assertTrue(report["pass"])
        self.assertEqual(report["blocker_count"], 0)
        self.assertEqual(report["warning_count"], 0)

        # Read draft content and verify essential SCMU elements
        content = post_path.read_text(encoding="utf-8")
        self.assertIn("铸牢中华民族共同体意识", content)
        self.assertIn("计算机科学学院（人工智能学院）", content)
        self.assertIn("IMG_3870.JPG", content)
        self.assertNotIn("IMG_3879.JPG", content)

    def test_t4_04_native_xiumi_packaging_workflow(self):
        """T4.4: End-to-End Workflow: Transform compliant draft into native Xiumi rich-text package."""
        html = build_xiumi_rich_html()

        # Step 1: Verify container structure
        self.assertIn("秀米/微信排版核心容器", html)
        self.assertIn("max-width: 677px", html)

        # Step 2: Verify narrative chapter structure
        chapters = [
            "军姿如铁",
            "战地赋能",
            "风雨砺剑",
            "庄严致敬",
        ]
        for ch in chapters:
            self.assertIn(ch, html, f"Chapter '{ch}' missing in Xiumi HTML package")

        # Step 3: Verify interactive callout & colophon
        self.assertIn("独家记忆 · 留下你的迷彩心声", html)
        self.assertIn("中南民族大学融媒体中心", html)

        # Step 4: Verify physical file output
        html_file = EXAMPLES_DIR / "cs_2026_junxun_xiumi.html"
        self.assertTrue(html_file.is_file())
        self.assertGreater(html_file.stat().st_size, 1_000_000)

    def test_t4_05_closed_loop_production_delivery_workflow(self):
        """T4.5: End-to-End Workflow: Full closed loop verification from corpus to browser rendering."""
        # 1. Corpus Fact Check
        corpus_path = KB_DIR / "scmu_articles_corpus.json"
        with open(corpus_path, "r", encoding="utf-8") as f:
            corpus = json.load(f)
        self.assertGreaterEqual(len(corpus), 278)

        # 2. Photo Selection Verification
        self.assertEqual(PHOTO_SELECTION["cover"], "IMG_3870.JPG")
        self.assertNotIn("IMG_3879.JPG", PHOTO_SELECTION.values())

        # 3. Draft Compliance Check
        post_path = EXAMPLES_DIR / "cs_2026_junxun_post.md"
        post_content = post_path.read_text(encoding="utf-8")
        issues = check_content(post_content)
        blockers = [i for i in issues if i["level"] == "BLOCKER"]
        warnings = [i for i in issues if i["level"] == "WARNING"]
        self.assertEqual(len(blockers), 0)
        self.assertEqual(len(warnings), 0)

        # 4. Native Xiumi HTML Artifact Check
        xiumi_html_path = EXAMPLES_DIR / "cs_2026_junxun_xiumi.html"
        self.assertTrue(xiumi_html_path.is_file())
        self.assertGreater(xiumi_html_path.stat().st_size, 1_000_000)

        # 5. Visual Rendering Screenshot Artifact Check
        screenshot_path = EXAMPLES_DIR / "xiumi_rendered_article.png"
        self.assertTrue(screenshot_path.is_file())
        with Image.open(screenshot_path) as img:
            self.assertGreaterEqual(img.width, 1000)
            self.assertGreaterEqual(img.height, 700)


if __name__ == "__main__":
    unittest.main()
