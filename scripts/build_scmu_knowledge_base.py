#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中南民族大学官方语料知识库爬取与构建脚本
从中南民族大学新闻网及官方新媒体归档抓取优质文章，进行数据清洗与结构化整理。
"""

import os
import sys
import re
import json
import base64
import time
import urllib.request
import urllib.parse

BASE_URL = "https://www.scuec.edu.cn/xww"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_html(raw_html):
    """清洗HTML正文，去除样式、脚本、空行与无关字符"""
    text = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # 将段落和换行转为自然换行
    text = re.sub(r'</?(p|br|div|h[1-6]|li|tr)[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    # 处理HTML实体
    text = text.replace('&nbsp;', ' ').replace('&ldquo;', '“').replace('&rdquo;', '”')
    text = text.replace('&lsquo;', '‘').replace('&rsquo;', '’').replace('&mdash;', '—')
    text = text.replace('&hellip;', '…').replace('&middot;', '·')
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n\n'.join(lines)

def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.read().decode('utf-8', errors='ignore')
    except Exception as e:
        # print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def parse_article(href, category_hint=""):
    """解析单篇文章的标题、时间、来源、作者、正文"""
    if not href.startswith('http'):
        url = f"{BASE_URL}/{href}"
    else:
        url = href
        
    html = fetch_url(url)
    if not html:
        return None

    # Title
    t_m = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
    title = ""
    if t_m:
        title = t_m.group(1).split('-')[0].strip()

    # Publish Date
    date_m = re.search(r'发布时间[：:]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', html)
    date = date_m.group(1) if date_m else ""

    # Source & Author
    src_m = re.search(r'来源[：:]\s*([^&<\s]+)', html)
    source = src_m.group(1).strip() if src_m else ""
    auth_m = re.search(r'作者[：:]\s*([^&<\s]+)', html)
    author = auth_m.group(1).strip() if auth_m else ""

    # Content
    content_m = re.search(r'id=[\"\']vsb_content[\"\'][^>]*>(.*?)</div>\s*<div', html, re.DOTALL)
    if not content_m:
        content_m = re.search(r'class=[\"\'][^\"]*content[^\"]*[\"\'][^>]*>(.*?)</div>', html, re.DOTALL)
    
    body = ""
    if content_m:
        body = clean_html(content_m.group(1))

    if not title or len(body) < 50:
        return None

    return {
        "title": title,
        "date": date,
        "source": source,
        "author": author,
        "url": url,
        "category": category_hint,
        "content": body
    }

def search_articles(keyword, max_pages=3):
    """通过检索接口获取相关文章链接"""
    b64_kw = base64.b64encode(keyword.encode('utf-8')).decode('ascii')
    articles_meta = []
    
    for page in range(1, max_pages + 1):
        search_url = f"{BASE_URL}/search.jsp?wbtreeid=1001&searchScope=0&currentnum={page}&newskeycode2={b64_kw}"
        html = fetch_url(search_url)
        if not html:
            break
        matches = re.findall(r'<a[^>]+href=[\"\'](info/[^\"]+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
        for href, raw_title in matches:
            clean_t = re.sub(r'<[^>]+>', '', raw_title).strip()
            if clean_t and not any(a['href'] == href for a in articles_meta):
                articles_meta.append({"href": href, "title": clean_t, "keyword": keyword})
        time.sleep(0.1)
    return articles_meta

def crawl_column(column_file, category_name, max_pages=3):
    """抓取具体栏目下的文章"""
    articles_meta = []
    base_col = column_file.replace('.htm', '')
    for page in range(1, max_pages + 1):
        if page == 1:
            url = f"{BASE_URL}/{column_file}"
        else:
            url = f"{BASE_URL}/{base_col}/{page}.htm"
        html = fetch_url(url)
        if not html:
            break
        matches = re.findall(r'<a[^>]+href=[\"\'](info/[^\"]+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
        for href, raw_title in matches:
            clean_t = re.sub(r'<[^>]+>', '', raw_title).strip()
            if clean_t and not any(a['href'] == href for a in articles_meta):
                articles_meta.append({"href": href, "title": clean_t, "keyword": category_name})
        time.sleep(0.1)
    return articles_meta

def main():
    print("开始抓取中南民族大学官方语料...")
    all_targets = []
    
    # 1. 核心关键词检索
    keywords = ["军训", "迎新", "双塔", "南湖", "青春", "计算机", "校友", "志愿服务"]
    for kw in keywords:
        print(f"正在检索关键词: {kw}")
        items = search_articles(kw, max_pages=3)
        print(f"  -> 获取到 {len(items)} 篇候选链接")
        all_targets.extend(items)
        
    # 2. 栏目归类抓取
    columns = [
        ("mdkx.htm", "民大要闻"),
        ("stxy.htm", "南湖快讯"),
        ("jxky.htm", "双塔校园"),
        ("mdrw.htm", "民大人物")
    ]
    for col, cname in columns:
        print(f"正在抓取栏目: {cname} ({col})")
        items = crawl_column(col, cname, max_pages=2)
        print(f"  -> 获取到 {len(items)} 篇候选链接")
        all_targets.extend(items)
        
    # 去重
    unique_targets = {}
    for item in all_targets:
        if item['href'] not in unique_targets:
            unique_targets[item['href']] = item
            
    print(f"去重后共需解析 {len(unique_targets)} 篇官方文章")
    
    corpus = []
    out_dir = "/Users/xbpd/Project/scmu-wechat-skill/references/scmu_knowledge_base"
    os.makedirs(out_dir, exist_ok=True)
    
    count = 0
    for href, meta in unique_targets.items():
        count += 1
        print(f"[{count}/{len(unique_targets)}] 解析: {meta['title'][:25]}...")
        art = parse_article(href, category_hint=meta['keyword'])
        if art:
            corpus.append(art)
        time.sleep(0.05)
        
    print(f"成功抓取并清洗 {len(corpus)} 篇有效文章！")
    
    # 保存完整 JSON 语料库
    json_path = os.path.join(out_dir, "scmu_articles_corpus.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    print(f"已保存完整 JSON 语料库至: {json_path}")
    
    # 提炼军训专题语料库
    military_articles = [a for a in corpus if "军训" in a['title'] or "军训" in a['content'] or "迷彩" in a['content']]
    print(f"筛选出军训专项文章 {len(military_articles)} 篇")
    
    mil_md_path = os.path.join(out_dir, "military_training_corpus.md")
    with open(mil_md_path, "w", encoding="utf-8") as f:
        f.write("# 中南民族大学历届新生军训官方报道与真实语料库\n\n")
        f.write(f"> 本专题收录了中南民族大学新闻网与新媒体历年来关于新生军训的深度报道、人物专访、特写及金句汇总，共收录 {len(military_articles)} 篇核心文献。\n\n")
        f.write("---\n\n")
        for i, a in enumerate(military_articles, 1):
            f.write(f"## {i}. {a['title']}\n")
            f.write(f"- **发布日期**：{a['date']}\n")
            f.write(f"- **来源**：{a['source']} | **作者**：{a['author']}\n")
            f.write(f"- **原文链接**：[{a['url']}]({a['url']})\n\n")
            f.write("### 报道正文摘录\n\n")
            f.write(a['content'] + "\n\n")
            f.write("---\n\n")
    print(f"已生成军训专题语料库: {mil_md_path}")

if __name__ == "__main__":
    main()
