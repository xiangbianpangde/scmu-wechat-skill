#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中南民族大学官方知识库检索与溯源 CLI 工具 (SCMU KB Query Tool)

支持关键词全文检索、倒排索引命中、分类与标签筛选、经典金句检索、
标志性意象统计分析、ANSI 彩色高亮摘要以及结构化 JSON 输出。
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Any, Optional

# Resolve paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
KB_DIR = os.path.join(PROJECT_DIR, "references", "scmu_knowledge_base")

CORPUS_PATH = os.path.join(KB_DIR, "scmu_articles_corpus.json")
INDEX_PATH = os.path.join(KB_DIR, "kb_index.json")
QUOTES_PATH = os.path.join(KB_DIR, "golden_quotes.json")


class ANSI:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_YELLOW = "\033[43;30m"
    BG_CYAN = "\033[46;30m"


def supports_color() -> bool:
    """Check if standard output supports ANSI escape codes."""
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    return True


def load_json(filepath: str) -> Any:
    if not os.path.isfile(filepath):
        print(f"Error: Required file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def highlight_text(text: str, query: str, use_ansi: bool = True) -> str:
    """Highlight query keyword in text using ANSI colors or markdown symbols."""
    if not query:
        return text
    try:
        escaped = re.escape(query)
        pattern = re.compile(f"({escaped})", re.IGNORECASE)
        if use_ansi:
            return pattern.sub(f"{ANSI.BOLD}{ANSI.YELLOW}\\1{ANSI.RESET}", text)
        else:
            return pattern.sub(r"【\1】", text)
    except Exception:
        return text


def extract_snippets(content: str, query: str, max_snippets: int = 3, window: int = 60, use_ansi: bool = True) -> List[str]:
    """Extract contextual snippets around query occurrences."""
    if not query:
        clean = " ".join(content.split())
        return [clean[:160] + ("..." if len(clean) > 160 else "")]

    content_clean = " ".join(content.split())
    try:
        escaped = re.escape(query)
        matches = list(re.finditer(escaped, content_clean, re.IGNORECASE))
    except Exception:
        matches = []

    if not matches:
        return [content_clean[:140] + ("..." if len(content_clean) > 140 else "")]

    snippets = []
    used_ranges = []

    for m in matches:
        start = max(0, m.start() - window)
        end = min(len(content_clean), m.end() + window)

        overlap = False
        for s_old, e_old in used_ranges:
            if not (end < s_old or start > e_old):
                overlap = True
                break
        if overlap:
            continue

        used_ranges.append((start, end))
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(content_clean) else ""
        raw_snip = prefix + content_clean[start:end] + suffix
        snippets.append(highlight_text(raw_snip, query, use_ansi=use_ansi))

        if len(snippets) >= max_snippets:
            break

    return snippets


def query_articles(
    corpus: List[Dict[str, Any]],
    index_data: Dict[str, Any],
    query: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 10,
    use_ansi: bool = True
) -> List[Dict[str, Any]]:
    """Filter and rank articles matching the search criteria."""
    tag_map = {t: set(meta["article_ids"]) for t, meta in index_data.get("tags", {}).items()}
    cat_map = {c: set(meta["article_ids"]) for c, meta in index_data.get("categories", {}).items()}

    matched_ids = set(range(len(corpus)))

    # Category filter
    if category:
        cat_clean = category.strip()
        matched_cat_ids = set()
        for c_name, ids in cat_map.items():
            if cat_clean.lower() in c_name.lower():
                matched_cat_ids.update(ids)
        matched_ids.intersection_update(matched_cat_ids)

    # Tag filter
    if tag:
        tag_clean = tag.strip()
        matched_tag_ids = set()
        for t_name, ids in tag_map.items():
            if tag_clean.lower() in t_name.lower():
                matched_tag_ids.update(ids)
        matched_ids.intersection_update(matched_tag_ids)

    # Query keyword search & scoring
    scored_results = []
    q_clean = query.strip() if query else ""

    articles_dict = index_data.get("articles", {})

    for art_id in matched_ids:
        art = corpus[art_id]
        title = art.get("title", "")
        content = art.get("content", "")

        score = 0
        match_count = 0
        if q_clean:
            try:
                title_hits = len(re.findall(re.escape(q_clean), title, re.IGNORECASE))
                content_hits = len(re.findall(re.escape(q_clean), content, re.IGNORECASE))
            except Exception:
                title_hits = title.count(q_clean)
                content_hits = content.count(q_clean)
            match_count = title_hits + content_hits

            # Inverted index boost
            if q_clean in index_data.get("inverted_index", {}):
                inv_matches = index_data["inverted_index"][q_clean]["articles"]
                for item in inv_matches:
                    if item["id"] == art_id:
                        score += item["count"] * 2

            if match_count == 0 and score == 0:
                continue

            score += title_hits * 15 + content_hits * 2
        else:
            score = 1

        snippets = extract_snippets(content, q_clean, max_snippets=2, use_ansi=use_ansi)
        clean_snippets = extract_snippets(content, q_clean, max_snippets=2, use_ansi=False)

        # Retrieve tags for this article from index metadata
        art_tags = []
        articles_data = index_data.get("articles", [])
        if isinstance(articles_data, dict):
            art_entry = articles_data.get(str(art_id), {})
        elif isinstance(articles_data, list) and art_id < len(articles_data):
            art_entry = articles_data[art_id]
        else:
            art_entry = {}

        if isinstance(art_entry, dict):
            art_tags = art_entry.get("tags", [])

        scored_results.append({
            "id": art_id,
            "title": title,
            "date": art.get("date", ""),
            "category": art.get("category", ""),
            "source": art.get("source", ""),
            "author": art.get("author", ""),
            "url": art.get("url", ""),
            "tags": art_tags,
            "score": score,
            "match_count": match_count,
            "snippets": snippets,
            "clean_snippets": clean_snippets
        })

    # Sort results
    if q_clean:
        scored_results.sort(key=lambda x: (x["score"], x["date"]), reverse=True)
    else:
        scored_results.sort(key=lambda x: x["date"], reverse=True)

    if limit > 0:
        return scored_results[:limit]
    return scored_results


def query_quotes(
    quotes_data: Dict[str, Any],
    query: Optional[str] = None,
    theme: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10,
    use_ansi: bool = True
) -> List[Dict[str, Any]]:
    """Filter and match golden quotes."""
    all_quotes = quotes_data.get("quotes", [])
    results = []
    q_clean = query.strip().lower() if query else ""
    t_clean = (theme or category or "").strip().lower()

    for item in all_quotes:
        # Theme filter
        if t_clean:
            item_theme = item.get("theme", "").lower()
            item_cat = item.get("category", "").lower()
            if t_clean not in item_theme and t_clean not in item_cat:
                continue

        # Query filter
        if q_clean:
            match_fields = [
                item.get("quote", ""),
                item.get("context", ""),
                item.get("speaker", ""),
                item.get("title", ""),
                item.get("article_title", ""),
                " ".join(item.get("keywords", []))
            ]
            combined = " ".join(match_fields).lower()
            if q_clean not in combined:
                continue

        # Format highlighted quote
        hl_quote = highlight_text(item["quote"], query if query else "", use_ansi=use_ansi)
        hl_context = highlight_text(item["context"], query if query else "", use_ansi=use_ansi)

        item_copy = dict(item)
        item_copy["highlighted_quote"] = hl_quote
        item_copy["highlighted_context"] = hl_context
        results.append(item_copy)

    if limit > 0:
        return results[:limit]
    return results


def print_terminal_articles(results: List[Dict[str, Any]], query: Optional[str], total_found: int, limit: int, use_ansi: bool):
    """Render search results nicely in terminal."""
    col_cyan = ANSI.CYAN if use_ansi else ""
    col_bold = ANSI.BOLD if use_ansi else ""
    col_yellow = ANSI.YELLOW if use_ansi else ""
    col_green = ANSI.GREEN if use_ansi else ""
    col_dim = ANSI.DIM if use_ansi else ""
    col_reset = ANSI.RESET if use_ansi else ""

    print(f"\n{col_bold}================================================================================{col_reset}")
    header_info = f"中南民族大学官方语料知识库检索结果 (SCMU Knowledge Base Search)"
    if query:
        header_info += f" | 关键词: '{col_yellow}{query}{col_reset}{col_bold}'"
    print(f"{col_bold}{header_info}{col_reset}")
    display_count = min(len(results), limit) if limit > 0 else len(results)
    print(f"{col_dim}共找到 {total_found} 篇匹配报道 (展示前 {display_count} 条){col_reset}")
    print(f"{col_bold}================================================================================{col_reset}\n")

    if not results:
        print(f"  {col_yellow}共找到 0 篇匹配报道。未检索到符合条件的官方报道，建议调整搜索词、栏目或标签再次查询。{col_reset}\n")
        return

    for idx, r in enumerate(results, 1):
        hl_title = highlight_text(r["title"], query if query else "", use_ansi=use_ansi)
        tag_str = ", ".join(r.get("tags", [])) if r.get("tags") else "无"

        print(f"{col_bold}[{idx}] {hl_title}{col_reset}")
        print(f"  {col_dim}• 发布日期:{col_reset} {r['date']}  {col_dim}| 栏目:{col_reset} {r['category']}  {col_dim}| 标签:{col_reset} {tag_str}")
        if r.get("source") or r.get("author"):
            print(f"  {col_dim}• 来源/作者:{col_reset} {r.get('source', '')} / {r.get('author', '')}")
        print(f"  {col_dim}• 官方出处 URL:{col_reset} {col_cyan}{r['url']}{col_reset}")
        
        if r.get("snippets"):
            print(f"  {col_dim}• 报道文段摘录:{col_reset}")
            for snip in r["snippets"]:
                print(f"    {snip}")
        print()


def print_terminal_quotes(quotes: List[Dict[str, Any]], query: Optional[str], theme: Optional[str], use_ansi: bool):
    """Render golden quotes nicely in terminal."""
    col_cyan = ANSI.CYAN if use_ansi else ""
    col_bold = ANSI.BOLD if use_ansi else ""
    col_yellow = ANSI.YELLOW if use_ansi else ""
    col_green = ANSI.GREEN if use_ansi else ""
    col_dim = ANSI.DIM if use_ansi else ""
    col_reset = ANSI.RESET if use_ansi else ""

    print(f"\n{col_bold}================================================================================{col_reset}")
    header_info = "中南民族大学官方经典金句摘录 (SCMU Golden Quotes)"
    if theme:
        header_info += f" | 主题: '{col_green}{theme}{col_reset}{col_bold}'"
    if query:
        header_info += f" | 关键词: '{col_yellow}{query}{col_reset}{col_bold}'"
    print(f"{col_bold}{header_info}{col_reset}")
    print(f"{col_dim}共检索到 {len(quotes)} 条高契合度经典金句{col_reset}")
    print(f"{col_bold}================================================================================{col_reset}\n")

    if not quotes:
        print(f"  {col_yellow}共找到 0 条金句。未检索到符合条件的经典金句。{col_reset}\n")
        return

    for idx, q in enumerate(quotes, 1):
        print(f"{col_bold}[金句 {idx}] 【{q['theme']}】 {col_dim}(ID: {q['id']}){col_reset}")
        print(f"  {col_green}{col_bold}“{q['highlighted_quote']}”{col_reset}")
        print(f"  {col_dim}• 发言人/背景:{col_reset} {q.get('speaker', '')} — {q['highlighted_context']}")
        print(f"  {col_dim}• 出处文章:{col_reset} 《{q.get('title') or q.get('article_title')}》 ({q['date']})")
        print(f"  {col_dim}• 原文溯源链接:{col_reset} {col_cyan}{q['url']}{col_reset}")
        print()


def print_stats(index_data: Dict[str, Any], quotes_data: Dict[str, Any], json_output: bool, use_ansi: bool):
    """Display knowledge base statistics."""
    meta = index_data.get("metadata", {})
    categories = index_data.get("categories", {})
    tags = index_data.get("tags", {})
    imagery = index_data.get("imagery_keywords", {})
    q_meta = quotes_data.get("metadata", {})

    stats_payload = {
        "title": meta.get("title", ""),
        "total_articles": meta.get("total_articles", 0),
        "indexed_keywords_count": meta.get("indexed_keywords_count", 0),
        "categories": {k: v["count"] for k, v in categories.items()},
        "tags": {k: v["count"] for k, v in tags.items()},
        "imagery_keywords": {k: {"doc_freq": v["doc_freq"], "total_freq": v["total_freq"], "imagery_type": v.get("imagery_type", "")} for k, v in imagery.items()},
        "golden_quotes": {
            "total_quotes": q_meta.get("total_quotes", 0),
            "theme_counts": q_meta.get("theme_counts", {})
        }
    }

    if json_output:
        print(json.dumps(stats_payload, ensure_ascii=False, indent=2))
        return

    col_cyan = ANSI.CYAN if use_ansi else ""
    col_bold = ANSI.BOLD if use_ansi else ""
    col_yellow = ANSI.YELLOW if use_ansi else ""
    col_green = ANSI.GREEN if use_ansi else ""
    col_dim = ANSI.DIM if use_ansi else ""
    col_reset = ANSI.RESET if use_ansi else ""

    print(f"\n{col_bold}================================================================================{col_reset}")
    print(f"{col_bold}中南民族大学官方语料知识库全景统计报表（知识库整体统计） (SCMU KB Statistics){col_reset}")
    print(f"{col_bold}================================================================================{col_reset}")
    print(f"📊 {col_bold}基础规模{col_reset}: 收录官方深度报道 {col_green}{meta.get('total_articles', 0)}{col_reset} 篇 | 倒排关键词 {col_yellow}{meta.get('indexed_keywords_count', 0)}{col_reset} 个 | 经典金句 {col_cyan}{q_meta.get('total_quotes', 0)}{col_reset} 条\n")

    print(f"📁 {col_bold}报道栏目分布 (Categories){col_reset}:")
    for cat_name, info in sorted(categories.items(), key=lambda x: x[1]["count"], reverse=True):
        print(f"   • {cat_name:<10}: {info['count']:>3} 篇")
    print()

    print(f"🏷️ {col_bold}语义标签分布 (Semantic Tags){col_reset}:")
    for tag_name, info in sorted(tags.items(), key=lambda x: x[1]["count"], reverse=True):
        print(f"   • {tag_name:<10}: {info['count']:>3} 篇 {col_dim}({info.get('description', '')[:25]}...){col_reset}")
    print()

    print(f"🏛️ {col_bold}高频标志性校园意象 (High-Frequency Imagery Keywords){col_reset}:")
    for kw, info in sorted(imagery.items(), key=lambda x: x[1]["total_freq"], reverse=True):
        extra = f" [文档数: {info['doc_freq']}, 总频次: {info['total_freq']}]"
        print(f"   • {col_yellow}{kw:<6}{col_reset}: {info.get('imagery_type', ''):<14} {extra}")
    print()

    print(f"💬 {col_bold}经典金句主题分布 (Golden Quotes by Theme){col_reset}:")
    for th, cnt in sorted(q_meta.get("theme_counts", {}).items(), key=lambda x: x[1], reverse=True):
        print(f"   • {th:<14}: {cnt:>2} 条")
    print(f"{col_bold}================================================================================{col_reset}\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="中南民族大学官方知识库检索与溯源 CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  python3 scripts/query_kb.py --query 军训
  python3 scripts/query_kb.py --query 双塔 --limit 3
  python3 scripts/query_kb.py --query 石榴籽 --json
  python3 scripts/query_kb.py --category 军训 --limit 5
  python3 scripts/query_kb.py --tag 民族团结
  python3 scripts/query_kb.py --quotes
  python3 scripts/query_kb.py --quotes --theme 军训淬炼
  python3 scripts/query_kb.py --quotes --query 迷彩
  python3 scripts/query_kb.py --stats
"""
    )
    parser.add_argument("-q", "--query", type=str, default="", help="检索关键词（如：军训、双塔、南湖、石榴籽、急救等）")
    parser.add_argument("-c", "--category", type=str, default="", help="按栏目分类过滤（如：军训、迎新、南湖、青春、计算机、民大人物等）")
    parser.add_argument("-t", "--tag", type=str, default="", help="按语义标签过滤（如：军训淬炼、民族团结、南湖风物、青春奋斗、校训精神等）")
    parser.add_argument("--quotes", "--golden-quotes", dest="quotes", action="store_true", help="查询与展示精选官方经典金句库")
    parser.add_argument("--theme", type=str, default="", help="金句主题过滤（如：军训淬炼、民族团结、南湖风物、青春奋斗、校训精神等）")
    parser.add_argument("-s", "--stats", action="store_true", help="显示知识库整体统计分析报表")
    parser.add_argument("-j", "--json", action="store_true", help="以结构化 JSON 格式输出结果")
    parser.add_argument("-n", "--limit", type=int, default=10, help="输出结果数量上限（默认: 10，0表示不限制）")
    parser.add_argument("--highlight", action="store_true", default=None, help="强制启用 ANSI 彩色高亮")
    parser.add_argument("--no-highlight", action="store_true", help="禁用 ANSI 彩色高亮")
    parser.add_argument("--strict", action="store_true", help="严格模式：若未检索到任何结果则退出码为 1")

    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.no_highlight or args.json:
        use_ansi = False
    elif args.highlight:
        use_ansi = True
    else:
        use_ansi = supports_color()

    # Load data files
    corpus = load_json(CORPUS_PATH)
    index_data = load_json(INDEX_PATH)
    quotes_data = load_json(QUOTES_PATH)

    # 1. Mode: Stats
    if args.stats:
        print_stats(index_data, quotes_data, json_output=args.json, use_ansi=use_ansi)
        sys.exit(0)

    # 2. Mode: Golden Quotes
    if args.quotes or args.theme:
        results = query_quotes(
            quotes_data=quotes_data,
            query=args.query,
            theme=args.theme,
            category=args.category,
            limit=args.limit,
            use_ansi=use_ansi
        )

        if args.json:
            clean_results = []
            for item in results:
                c = dict(item)
                c.pop("highlighted_quote", None)
                c.pop("highlighted_context", None)
                clean_results.append(c)
            out_obj = {
                "status": "success",
                "type": "golden_quotes",
                "total_matches": len(clean_results),
                "limit": args.limit,
                "query": args.query,
                "theme": args.theme,
                "results": clean_results,
                "quotes": clean_results
            }
            print(json.dumps(out_obj, ensure_ascii=False, indent=2))
        else:
            print_terminal_quotes(results, query=args.query, theme=args.theme, use_ansi=use_ansi)

        if args.strict and len(results) == 0:
            sys.exit(1)
        sys.exit(0)

    # 3. Mode: Search Articles
    if not (args.query or "").strip() and not (args.category or "").strip() and not (args.tag or "").strip():
        if args.json:
            out_obj = {
                "status": "success",
                "total_articles": len(corpus),
                "results": [],
                "message": "请使用 --query, --category, --tag, --quotes 或 --stats 查询知识库"
            }
            print(json.dumps(out_obj, ensure_ascii=False, indent=2))
        else:
            parser.print_help()
            print()
            print_stats(index_data, quotes_data, json_output=False, use_ansi=use_ansi)
        sys.exit(0)

    results = query_articles(
        corpus=corpus,
        index_data=index_data,
        query=args.query,
        category=args.category,
        tag=args.tag,
        limit=args.limit,
        use_ansi=use_ansi
    )

    if args.json:
        clean_results = []
        for r in results:
            c = dict(r)
            c.pop("clean_snippets", None)
            clean_results.append(c)
        out_obj = {
            "status": "success",
            "type": "articles",
            "query": args.query,
            "category": args.category,
            "tag": args.tag,
            "total_matches": len(results),
            "limit": args.limit,
            "results": clean_results
        }
        print(json.dumps(out_obj, ensure_ascii=False, indent=2))
    else:
        print_terminal_articles(
            results=results,
            query=args.query,
            total_found=len(results),
            limit=args.limit,
            use_ansi=use_ansi
        )

    if args.strict and len(results) == 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
