#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：check_compliance.py
"""

import sys
import unittest
from pathlib import Path

# 添加父目录至 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from check_compliance import check_content


class TestSCMUComplianceChecker(unittest.TestCase):

    def test_clean_content_passes(self):
        text = """# 喜报！中南民族大学荣获国家级教学成果一等奖

> 紧紧围绕铸牢中华民族共同体意识主线，深化教育教学改革。

### ▍深耕笃行
中南民族大学坚持“笃信好学，自然宽和”的校训精神。

[配图位置 1]：双塔全景照片
配图说明：南湖之畔的南区双塔

---
文案 ｜ 融媒记者
排版 ｜ 融媒编辑
终审 ｜ 党委宣传部
来源 ｜ 中南民族大学融媒体中心
"""
        issues = check_content(text)
        blockers = [i for i in issues if i["level"] == "BLOCKER"]
        warnings = [i for i in issues if i["level"] == "WARNING"]
        self.assertEqual(len(blockers), 0, "合规文本不应有 BLOCKER")
        self.assertEqual(len(warnings), 0, "合规文本不应有 WARNING")

    def test_political_blocker_detection(self):
        # 测试“铸造中华民族共同体意识”应被阻断
        bad_text = "学校致力于铸造中华民族共同体意识。"
        issues = check_content(bad_text)
        blocker_ids = [i["id"] for i in issues if i["level"] == "BLOCKER"]
        self.assertIn("POL-001", blocker_ids)

        # 测试宗教进校园违规
        bad_religion = "欢迎广大师生参与周末校园传教活动。"
        issues_rel = check_content(bad_religion)
        blocker_rel = [i["id"] for i in issues_rel if i["level"] == "BLOCKER"]
        self.assertIn("POL-004", blocker_rel)

        # 测试办学主管单位错误
        bad_dept = "作为教育部直属的中南民族大学，近年来取得重大突破。"
        issues_dept = check_content(bad_dept)
        blocker_dept = [i["id"] for i in issues_dept if i["level"] == "BLOCKER"]
        self.assertIn("POL-005", blocker_dept)

    def test_scmu_warnings_detection(self):
        # 测试校名旧称中南民院
        bad_name = "今天中南民院迎来了一批新同学。"
        issues = check_content(bad_name)
        warning_ids = [i["id"] for i in issues if i["level"] == "WARNING"]
        self.assertIn("SCMU-001", warning_ids)

        # 测试校训笔误：自然和谐
        bad_motto = "民大学子秉承笃信好学，自然和谐的精神。"
        issues_motto = check_content(bad_motto)
        warning_motto = [i["id"] for i in issues_motto if i["level"] == "WARNING"]
        self.assertIn("SCMU-003", warning_motto)

        # 测试地标笔误：民俗博物馆
        bad_museum = "欢迎大家参观我校民俗博物馆。"
        issues_mus = check_content(bad_museum)
        warning_mus = [i["id"] for i in issues_mus if i["level"] == "WARNING"]
        self.assertIn("SCMU-005", warning_mus)


if __name__ == "__main__":
    unittest.main()
