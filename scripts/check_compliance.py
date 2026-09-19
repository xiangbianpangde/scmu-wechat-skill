#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中南民族大学官方微信公众号推文三审三校质检脚本
SCMU WeChat Compliance & Quality Checker

功能：
1. 离线检查推文是否存在政治红线、涉民族宗教违规（BLOCKER）
2. 检查校名、校训、校园地标及学院名称常见笔误与历史称谓误用（WARNING）
3. 检查微信排版格式、三审落款、标题标点等新媒体规范（SUGGESTION）
4. 支持终端彩色输出与 JSON 机器可读格式，支持 CI/CD 自动化集成

使用方式：
    python3 check_compliance.py draft.md
    python3 check_compliance.py draft.md --strict
    python3 check_compliance.py draft.md --json
    cat draft.md | python3 check_compliance.py -
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Colors:
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


# 规则定义字典
RULES = [
    # ==========================================
    # 1. BLOCKER: 政治与涉民族宗教政策红线
    # ==========================================
    {
        "id": "POL-001",
        "level": "BLOCKER",
        "pattern": r"铸[造就]中华民族共同体意识",
        "message": "“铸牢中华民族共同体意识”表述错误，规范动词必须为“铸牢”，不得使用“铸造”或“铸就”。",
        "suggestion": "铸牢中华民族共同体意识"
    },
    {
        "id": "POL-002",
        "level": "BLOCKER",
        "pattern": r"中华民族命运共同体意识",
        "message": "提法混淆。官方规范提法为“铸牢中华民族共同体意识”；“人类命运共同体”不可与中华民族共同体混编。",
        "suggestion": "中华民族共同体意识"
    },
    {
        "id": "POL-003",
        "level": "BLOCKER",
        "pattern": r"(泛清真化|清真水|清真盐|清真纸|清真通道|清真专用道)",
        "message": "严防“泛清真化”倾向。“清真”概念严格限于清真食品范畴，严禁泛化至日用品、场所或公共制度。",
        "suggestion": "删除不当清真泛化表述，严格遵守国家民族宗教政策。"
    },
    {
        "id": "POL-004",
        "level": "BLOCKER",
        "pattern": r"(校园传教|校园布道|宗教进校园|开展弥撒|主日崇拜)",
        "message": "严重违背“教育与宗教相分离”根本原则。高校官方媒体严禁宣传校园宗教活动。",
        "suggestion": "立即删除涉宗教活动宣传内容。"
    },
    {
        "id": "POL-005",
        "level": "BLOCKER",
        "pattern": r"(教育部直属的中南民族大学|中南民族大学是教育部直属)",
        "message": "办学主管单位错误。中南民族大学是“国家民族事务委员会（国家民委）直属综合性普通高等院校”，非教育部直属高校。",
        "suggestion": "国家民族事务委员会直属综合性高校（或国家民委直属高校）"
    },

    # ==========================================
    # 2. WARNING: 校名、校训、历史称谓与地标严重笔误
    # ==========================================
    {
        "id": "SCMU-001",
        "level": "WARNING",
        "pattern": r"(中南民院|中南民族学院(?!（原|历史|创办|更名))",
        "message": "检测到使用历史曾用名“中南民院”或“中南民族学院”。学校已于2002年更名为中南民族大学，现行报道一律使用“中南民族大学”或“中南民大”。",
        "suggestion": "中南民族大学 或 中南民大"
    },
    {
        "id": "SCMU-002",
        "level": "WARNING",
        "pattern": r"(民大大学|中南民大学校|中南民族学院大学)",
        "message": "校名语病重叠错误。",
        "suggestion": "中南民族大学 或 中南民大"
    },
    {
        "id": "SCMU-003",
        "level": "WARNING",
        "pattern": r"笃信好学[，,\s]*自然(和谐|平和|温和|平实)",
        "message": "校训文字错写。中南民族大学校训为“笃信好学 自然宽和”，“宽和”二字不得擅改为“和谐”或“平和”。",
        "suggestion": "笃信好学 自然宽和"
    },
    {
        "id": "SCMU-004",
        "level": "WARNING",
        "pattern": r"笃学好[古学][，,\s]*自然宽和",
        "message": "校训首句错写。校训为“笃信好学 自然宽和”。",
        "suggestion": "笃信好学 自然宽和"
    },
    {
        "id": "SCMU-005",
        "level": "WARNING",
        "pattern": r"(?:中南|民大|校园|我校)?(?:民俗博物馆|民族博物馆)",
        "message": "地标名称错误。全国首座高校民族学专题博物馆全称为“民族学博物馆”，不可遗漏“学”字，亦非“民俗博物馆”。",
        "suggestion": "民族学博物馆"
    },
    {
        "id": "SCMU-006",
        "level": "WARNING",
        "pattern": r"(汤逊湖之[畔滨]|东湖之[畔滨])(?=.*(双塔|民大|南区|平顶山))",
        "message": "地理位置混淆。中南民族大学毗邻武昌南湖，并非东湖或汤逊湖。",
        "suggestion": "南湖之滨 或 南湖之畔"
    },
    {
        "id": "SCMU-007",
        "level": "WARNING",
        "pattern": r"文学院(?=.*(中南民大|我校|民大))",
        "message": "学院全称可能有误。中南民大该学科院系现官方全称为“文学与新闻传播学院”（简称文传学院）。",
        "suggestion": "文学与新闻传播学院（文传学院）"
    },

    # ==========================================
    # 3. SUGGESTION: 微信新媒体排版与审校规范
    # ==========================================
    {
        "id": "FMT-001",
        "level": "SUGGESTION",
        "pattern": r"^#\s+.*[。！!？?]\s*$",
        "message": "微信推文一级大标题末尾建议不使用句号或感叹号，保持紧凑和视觉美感。",
        "suggestion": "去掉标题末尾标点符号"
    },
    {
        "id": "FMT-002",
        "level": "SUGGESTION",
        "pattern": r"“[^”]*$",
        "message": "检测到未闭合的左双引号“，请检查引号是否成对出现。",
        "suggestion": "补充右双引号”"
    }
]


def check_content(content: str) -> List[Dict]:
    """对文本内容逐行与全局进行合规质检"""
    issues = []
    lines = content.splitlines()

    # 1. 逐行规则扫描
    for line_idx, line in enumerate(lines, start=1):
        for rule in RULES:
            matches = list(re.finditer(rule["pattern"], line))
            for m in matches:
                issues.append({
                    "id": rule["id"],
                    "level": rule["level"],
                    "line": line_idx,
                    "column": m.start() + 1,
                    "matched_text": m.group(0),
                    "context": line.strip(),
                    "message": rule["message"],
                    "suggestion": rule["suggestion"],
                })

    # 2. 全文结构完整性检查
    # 检查文末官方融媒体中心/党委宣传部落款
    has_source = any(keyword in content for keyword in ["中南民族大学融媒体中心", "党委宣传部", "融媒体中心"])
    if not has_source and len(lines) > 10:
        issues.append({
            "id": "STRUC-001",
            "level": "SUGGESTION",
            "line": len(lines),
            "column": 1,
            "matched_text": "[缺少官方落款]",
            "context": lines[-1].strip() if lines else "",
            "message": "推文文末未检测到官方融媒体署名或审校落款（来源：中南民族大学融媒体中心 / 党委宣传部）。",
            "suggestion": "在推文末尾增加标准落款卡片：文案/排版/初审/终审/来源：中南民族大学融媒体中心。"
        })

    # 检查配图占位符
    has_images = any(keyword in content for keyword in ["[配图", "📷", "![", "<img"])
    if not has_images and len(lines) > 15:
        issues.append({
            "id": "STRUC-002",
            "level": "SUGGESTION",
            "line": 1,
            "column": 1,
            "matched_text": "[缺少配图标记]",
            "context": lines[0].strip() if lines else "",
            "message": "长篇推文未检测到配图位置标记（[配图位置] 或 📷）。图文并茂是微信排版的重要指标。",
            "suggestion": "在关键叙述段落后插入配图占位符及摄影说明。"
        })

    return issues


def render_terminal_report(issues: List[Dict], filepath: str, no_color: bool = False) -> int:
    """渲染终端彩色报告"""
    c_red = "" if no_color else Colors.RED
    c_yellow = "" if no_color else Colors.YELLOW
    c_cyan = "" if no_color else Colors.CYAN
    c_green = "" if no_color else Colors.GREEN
    c_bold = "" if no_color else Colors.BOLD
    c_reset = "" if no_color else Colors.RESET

    blockers = [i for i in issues if i["level"] == "BLOCKER"]
    warnings = [i for i in issues if i["level"] == "WARNING"]
    suggestions = [i for i in issues if i["level"] == "SUGGESTION"]

    print(f"\n{c_bold}======================================================{c_reset}")
    print(f"{c_bold}  中南民族大学微信推文三审三校合规质检报告{c_reset}")
    print(f"  待检文件: {filepath}")
    print(f"{c_bold}======================================================{c_reset}\n")

    if not issues:
        print(f"{c_green}✓ 恭喜！未检测到任何合规风险或格式问题，推文符合发布规范！{c_reset}\n")
        return 0

    for issue in issues:
        level = issue["level"]
        if level == "BLOCKER":
            lvl_str = f"{c_red}{c_bold}[阻断 BLOCKER]{c_reset}"
        elif level == "WARNING":
            lvl_str = f"{c_yellow}{c_bold}[警告 WARNING]{c_reset}"
        else:
            lvl_str = f"{c_cyan}{c_bold}[建议 SUGGEST]{c_reset}"

        print(f"{lvl_str} {c_bold}{issue['id']}{c_reset} 第 {issue['line']} 行, 第 {issue['column']} 列")
        print(f"  匹配词: \"{issue['matched_text']}\"")
        print(f"  上下文: {issue['context']}")
        print(f"  说明  : {issue['message']}")
        print(f"  建议  : {c_green}{issue['suggestion']}{c_reset}")
        print()

    print(f"{c_bold}---------------- 统计汇总 ----------------{c_reset}")
    print(f"  {c_red}阻断项 (BLOCKER)  : {len(blockers)}{c_reset}")
    print(f"  {c_yellow}警告项 (WARNING)  : {len(warnings)}{c_reset}")
    print(f"  {c_cyan}建议项 (SUGGEST)  : {len(suggestions)}{c_reset}")
    print(f"{c_bold}------------------------------------------{c_reset}\n")

    if blockers:
        print(f"{c_red}{c_bold}❌ 质检未通过：存在 {len(blockers)} 处严重违规/政治红线问题，严禁发布！{c_reset}\n")
        return 1
    elif warnings:
        print(f"{c_yellow}⚠️ 质检存疑：存在 {len(warnings)} 处校情校训或地标笔误，建议核对修正后发布。{c_reset}\n")
        return 0
    else:
        print(f"{c_green}✓ 核心要素核验通过，仅有排版优化建议。{c_reset}\n")
        return 0


def main():
    parser = argparse.ArgumentParser(description="中南民族大学官方微信推文合规与校情质检脚本")
    parser.add_argument("file", help="待检测的推文文件路径（Markdown 或 TXT），使用 '-' 表示读取标准输入")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    parser.add_argument("--no-color", action="store_true", help="禁用彩色终端输出")
    parser.add_argument("--strict", action="store_true", help="严格模式：若存在 WARNING 也返回非0退出码")

    args = parser.parse_args()

    if args.file == "-":
        content = sys.stdin.read()
        target_name = "<stdin>"
    else:
        file_path = Path(args.file)
        if not file_path.is_file():
            print(f"错误：文件 {args.file} 不存在或不是普通文件。", file=sys.stderr)
            sys.exit(2)
        content = file_path.read_text(encoding="utf-8", errors="replace")
        target_name = str(file_path)

    issues = check_content(content)

    if args.json:
        result = {
            "file": target_name,
            "pass": not any(i["level"] == "BLOCKER" for i in issues),
            "total_issues": len(issues),
            "blocker_count": sum(1 for i in issues if i["level"] == "BLOCKER"),
            "warning_count": sum(1 for i in issues if i["level"] == "WARNING"),
            "suggestion_count": sum(1 for i in issues if i["level"] == "SUGGESTION"),
            "issues": issues,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if any(i["level"] == "BLOCKER" for i in issues) or (args.strict and any(i["level"] == "WARNING" for i in issues)):
            sys.exit(1)
        sys.exit(0)
    else:
        code = render_terminal_report(issues, target_name, no_color=args.no_color)
        if args.strict and any(i["level"] == "WARNING" for i in issues):
            sys.exit(1)
        sys.exit(code)


if __name__ == "__main__":
    main()
