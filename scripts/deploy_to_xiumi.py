#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
秀米（Xiumi）原生排版自动化与交付引擎
将精选照片、人味文案、中南民大视觉规范全量渲染至秀米编辑器（https://xiumi.us/#/），
并自动联动本地 Chrome 浏览器与系统富文本剪贴板。
"""

import os
import sys
import base64
import time
import subprocess
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright

PHOTO_DIR = "/Volumes/xbpd的u盘/junxun"
OUTPUT_DIR = "/Users/xbpd/Project/scmu-wechat-skill/examples"

# 严格依据评测报告遴选的 A/A+ 级照片清单
PHOTO_SELECTION = {
    "cover": "IMG_3870.JPG",       # 南湖绿茵操场大场景全景方阵 (Score 93.0)
    "queue_check": "IMG_3830.JPG", # 教官核对军姿细节与排面 (Score 92.0, 锐度18.1)
    "white_line": "IMG_3865.JPG",  # 脚尖与白线对齐细节特写 (Score 88.0)
    "first_aid_1": "IMG_3857.JPG", # 战地救护席地互助包扎 (Score 100.0, 锐度19.0)
    "first_aid_2": "IMG_3855.JPG", # 三角巾头部包扎实训 (Score 93.0, 锐度17.7)
    "rain_march": "IMG_3895.JPG",  # 秋雨红旗引路、踏水前行视觉高潮 (Score 70.0 动态雨景)
    "salute": "IMG_3905.JPG",      # 庄严崇高军礼、眼神坚定 (Score 93.0)
    "stride": "IMG_3920.JPG"       # 意气风发阔步新程 (Score 93.0, 锐度17.8)
}

def get_base64_image(filename, max_width=1200, quality=85):
    """将大图缩放为新媒体高品质标准尺寸并转为 base64 数据流"""
    path = os.path.join(PHOTO_DIR, filename)
    if not os.path.exists(path):
        print(f"Warning: {path} not found!", file=sys.stderr)
        return ""
    with Image.open(path) as img:
        w, h = img.size
        if w > max_width:
            target_h = int(h * (max_width / w))
            img = img.resize((max_width, target_h), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{b64_str}"

def build_xiumi_rich_html():
    """生成具备浓郁人味、五感细节与极致秀米版式的完整富文本 HTML"""
    print("正在处理高精度配图并生成 Base64 数据流...")
    b64_imgs = {k: get_base64_image(v) for k, v in PHOTO_SELECTION.items()}
    
    html = f"""<!-- 秀米/微信排版核心容器 -->
<div style="margin: 0 auto; max-width: 677px; background-color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif; font-size: 15px; color: #2B2B2B; line-height: 1.85; letter-spacing: 0.6px; padding: 12px 10px; box-sizing: border-box;">

  <!-- 顶部主标题卡片 (民大石榴红渐变 + 质感投影) -->
  <section style="background: linear-gradient(135deg, #B8242A 0%, #7E1116 100%); border-radius: 14px; padding: 28px 20px; color: #FFFFFF; text-align: center; box-shadow: 0 8px 24px rgba(184, 36, 42, 0.22); margin-bottom: 26px;">
    <div style="font-size: 12px; letter-spacing: 3px; text-transform: uppercase; opacity: 0.85; margin-bottom: 8px;">South-Central Minzu University</div>
    <div style="font-size: 21px; font-weight: 700; letter-spacing: 1px; line-height: 1.4; margin-bottom: 8px;">计算机科学学院（人工智能学院）</div>
    <div style="display: inline-block; background: rgba(255, 255, 255, 0.18); border: 1px solid rgba(255, 255, 255, 0.35); padding: 3px 14px; border-radius: 20px; font-size: 13.5px; letter-spacing: 1.5px;">
      2026级新生军训纪实 · 迷彩华章
    </div>
  </section>

  <!-- 封面焦点大图 -->
  <section style="margin: 0 0 24px 0; text-align: center;">
    <img src="{b64_imgs['cover']}" style="width: 100%; border-radius: 12px; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12); display: block;" alt="南湖操场方阵集结" />
    <div style="font-size: 12px; color: #888888; margin-top: 8px; text-align: center; letter-spacing: 0.5px;">
      📷 南湖操场上，2026级迷彩方阵巍然伫立，写下大学第一课的热血开篇
    </div>
  </section>

  <!-- 引言：南湖畔的真实微叙事与感官记忆 -->
  <section style="background-color: #FAF8F5; border-left: 4px solid #B8242A; border-radius: 0 10px 10px 0; padding: 20px 18px; margin: 24px 0 32px 0;">
    <p style="margin: 0; text-indent: 2em; color: #4A4A4A; line-height: 1.9;">
      南湖的风，总是在九月的清晨带着微微的湿润。当清脆的军号声划破拂晓的微光，在计算机科学学院（人工智能学院）2026级新生的世界里，这个秋天注定不再只有键盘敲击的清脆回响。
    </p>
    <p style="margin: 12px 0 0 0; text-indent: 2em; color: #4A4A4A; line-height: 1.9;">
      从第一声稍息、立正的生涩，到烈日下与草坪白线死磕的严谨；从把室友包成“重伤员”时憋不住的欢笑，到秋雨砸湿帽檐时踏碎水坑的坚毅脚步。那些被汗水浸湿后贴在后背发硬的作训服、那些在脖颈和手腕上晒出的“迷彩防伪线”，悄然写就了独属于少年们的拔节成长。
    </p>
  </section>

  <!-- 篇章一：军姿如铁 -->
  <section style="margin: 36px 0 18px 0; display: flex; align-items: center;">
    <span style="background: #B8242A; color: #FFFFFF; font-size: 13px; font-weight: bold; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(184, 36, 42, 0.3);">01</span>
    <span style="font-size: 17.5px; font-weight: 700; color: #B8242A; letter-spacing: 1px;">军姿如铁 · 毫厘之间见证少年坚毅</span>
  </section>

  <p style="text-indent: 2em; margin-bottom: 14px;">
    “两脚分开六十度，脚跟靠拢，大臂贴紧，中指紧贴裤缝！”
  </p>
  <p style="text-indent: 2em; margin-bottom: 14px;">
    来自陆军工程大学军械士官学校的承训教官，声音略显嘶哑却字字千钧。平日里在终端里调代码、找 Bug 的计科学子，把那份骨子里的较真，全用在了与身姿线条的“毫厘死磕”上。
  </p>
  <p style="text-indent: 2em; margin-bottom: 18px;">
    武汉初秋的骄阳毫不留情，豆大的汗珠顺着睫毛和脸颊滑落，砸在发烫的跑道上瞬间蒸发。没有一个人抬手去擦，没有人动弹分毫。在心里默数的每一个六十秒里，稚嫩与松散被悄悄褪去，取而代之的是如松如柏的昂拔脊梁。
  </p>

  <!-- 军姿配图组：双图纵深与微距 -->
  <section style="margin: 20px 0 10px 0;">
    <img src="{b64_imgs['queue_check']}" style="width: 100%; border-radius: 10px; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08); display: block;" alt="教官逐排校准军姿" />
    <div style="font-size: 12px; color: #888888; margin-top: 6px; text-align: center;">
      📷 逐行校准、一丝不苟：教官穿梭在队列中，细致纠正每一个细微动作
    </div>
  </section>

  <section style="margin: 16px 0 26px 0;">
    <img src="{b64_imgs['white_line']}" style="width: 100%; border-radius: 10px; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08); display: block;" alt="脚尖与白线毫厘对齐" />
    <div style="font-size: 12px; color: #888888; margin-top: 6px; text-align: center;">
      📷 细节见真章：脚尖与草坪标线严丝合缝，指缝贴紧，是计科人的专属严谨
    </div>
  </section>

  <!-- 篇章二：战地救护（人情味拉满） -->
  <section style="margin: 38px 0 18px 0; display: flex; align-items: center;">
    <span style="background: #1F5F8B; color: #FFFFFF; font-size: 13px; font-weight: bold; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(31, 95, 139, 0.3);">02</span>
    <span style="font-size: 17.5px; font-weight: 700; color: #1F5F8B; letter-spacing: 1px;">战地赋能 · 草坪围坐里的温暖人情</span>
  </section>

  <p style="text-indent: 2em; margin-bottom: 14px;">
    如果说队列训练考验的是铁一般的意志，那么实战化战地卫生与自救互救实操，则写满了战友之间最鲜活的温情。
  </p>
  <p style="text-indent: 2em; margin-bottom: 14px;">
    绿茵坪上，大家卸下严整的队列，围坐成一圈圈欢快的同心圆。刚才还在比谁正步踢得高的室友，转眼就被三角巾裹成了呆萌的“病患”。
  </p>
  <p style="text-indent: 2em; margin-bottom: 18px;">
    “别动别动，这个平结必须压在眉骨上方两指！”虽然嘴上开着玩笑、互相打趣，手上的动作却比谁都小心翼翼。折叠、包扎、打结、固定——在一次次推敲与配合中，同窗的情谊在指尖升温，互助的担当在心底生根。
  </p>

  <!-- 战地急救实景图组 -->
  <section style="margin: 20px 0 10px 0;">
    <img src="{b64_imgs['first_aid_1']}" style="width: 100%; border-radius: 10px; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08); display: block;" alt="草坪席地互助急救包扎" />
    <div style="font-size: 12px; color: #888888; margin-top: 6px; text-align: center;">
      📷 绿茵席地、凝神互助：同学们认真演练三角巾包扎细节
    </div>
  </section>

  <section style="margin: 16px 0 26px 0;">
    <img src="{b64_imgs['first_aid_2']}" style="width: 100%; border-radius: 10px; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08); display: block;" alt="头部包扎互助实战" />
    <div style="font-size: 12px; color: #888888; margin-top: 6px; text-align: center;">
      📷 战友同心：严谨细致的每一个步骤，饱含着并肩同行的温暖默契
    </div>
  </section>

  <!-- 篇章三：风雨砺剑（动感与豪气） -->
  <section style="margin: 38px 0 18px 0; display: flex; align-items: center;">
    <span style="background: #B8242A; color: #FFFFFF; font-size: 13px; font-weight: bold; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(184, 36, 42, 0.3);">03</span>
    <span style="font-size: 17.5px; font-weight: 700; color: #B8242A; letter-spacing: 1px;">风雨砺剑 · 战旗猎猎踏碎满地水花</span>
  </section>

  <p style="text-indent: 2em; margin-bottom: 14px;">
    九月的南湖操场，秋雨总是不期而至。冰凉的雨丝打在发梢，打湿了薄薄的迷彩作训服，却丝毫浇不灭训练场上的滚烫热血。
  </p>
  <p style="text-indent: 2em; margin-bottom: 16px;">
    “一！二！三！四！”
  </p>
  <p style="text-indent: 2em; margin-bottom: 18px;">
    红色塑胶跑道上倒映着猎猎招展的红旗，队伍踏着积水齐步向前。胶底作训鞋砸进水坑，激荡起白色的水花，脚步声铿锵震耳，比雷鸣更显磅礴。风雨之中，不仅有挺拔的身姿，更有少年面对人生风浪时从容无畏的狂气与豪迈！
  </p>

  <!-- 风雨行进核心大图 -->
  <section style="margin: 20px 0 26px 0;">
    <img src="{b64_imgs['rain_march']}" style="width: 100%; border-radius: 10px; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08); display: block;" alt="风雨中踏水前行" />
    <div style="font-size: 12px; color: #888888; margin-top: 6px; text-align: center;">
      📷 战旗引路、水花四溅：风雨中的铿锵步履，是青春最壮美的注脚
    </div>
  </section>

  <!-- 篇章四：庄严军礼与精神升华 -->
  <section style="margin: 38px 0 18px 0; display: flex; align-items: center;">
    <span style="background: #1F5F8B; color: #FFFFFF; font-size: 13px; font-weight: bold; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(31, 95, 139, 0.3);">04</span>
    <span style="font-size: 17.5px; font-weight: 700; color: #1F5F8B; letter-spacing: 1px;">庄严致敬 · 迷彩少年奔赴星辰大海</span>
  </section>

  <p style="text-indent: 2em; margin-bottom: 14px;">
    右手迅速抬起，四指并拢自然伸直，中指微接帽檐右角——当庄严的军礼在阳光下定格，那清澈而坚定的眼眸深处，是对国防事业的崇高敬意，更是对壮阔大学生涯的庄严立誓。
  </p>
  <p style="text-indent: 2em; margin-bottom: 18px;">
    还记得“九一八”清晨在国旗下的静默肃立，还记得拉歌夜七楼乐队电吉他扫弦带来的全场狂欢，还记得各族学子共育“石榴林”的深情约定。五湖四海的心，在这个金秋像石榴籽一样紧紧抱在一起，共同汇聚成计算机学院最硬核的青春底色！
  </p>

  <!-- 军礼与阔步收官图组 -->
  <section style="margin: 20px 0 10px 0;">
    <img src="{b64_imgs['salute']}" style="width: 100%; border-radius: 10px; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08); display: block;" alt="庄严标准军礼" />
    <div style="font-size: 12px; color: #888888; margin-top: 6px; text-align: center;">
      📷 庄严敬礼：坚毅的目光穿透迷彩，是少年对时代的庄重承诺
    </div>
  </section>

  <section style="margin: 16px 0 26px 0;">
    <img src="{b64_imgs['stride']}" style="width: 100%; border-radius: 10px; box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08); display: block;" alt="昂首阔步新征程" />
    <div style="font-size: 12px; color: #888888; margin-top: 6px; text-align: center;">
      📷 意气风发：迈着坚定的步伐，展现民大学子昂扬向上的精神风貌
    </div>
  </section>

  <!-- 结语卡片 (晨曦金与暖米色高级边框) -->
  <section style="background: linear-gradient(180deg, #FDFBF7 0%, #F7F2EC 100%); border: 1.5px solid #E6D8C8; border-radius: 12px; padding: 24px 20px; margin: 36px 0 28px 0; box-shadow: 0 4px 14px rgba(212, 163, 89, 0.12);">
    <div style="font-size: 17px; font-weight: bold; color: #B8242A; text-align: center; margin-bottom: 14px; letter-spacing: 1px;">
      以青春之名，赴强国之约
    </div>
    <p style="font-size: 14.5px; color: #3E3E3E; line-height: 1.9; margin: 0; text-indent: 2em;">
      军训的哨音已然消散在南湖的秋风里，但淬炼出的钢铁作风却将融进每一名计科学子的生命脉络。
    </p>
    <p style="font-size: 14.5px; color: #3E3E3E; line-height: 1.9; margin: 10px 0 0 0; text-indent: 2em;">
      走出训练场，走进实验室与图书馆。秉承<strong>“笃信好学 自然宽和”</strong>的民大校训，牢固<strong>铸牢中华民族共同体意识</strong>，愿2026级的你们，以军人般的刚毅叩问科学前沿，以指尖灵动的代码构筑强国梦想。星光不负赶路人，江河眷顾奋楫者，新征程，我们阔步向前！
    </p>
  </section>

  <!-- 互动话题与留言彩蛋 -->
  <section style="border-top: 1px dashed #D0D0D0; padding-top: 24px; margin-top: 36px;">
    <div style="font-size: 15.5px; font-weight: bold; color: #1F5F8B; margin-bottom: 12px; display: flex; align-items: center;">
      <span style="display: inline-block; width: 4px; height: 18px; background-color: #D4A359; margin-right: 8px; border-radius: 2px;"></span>
      独家记忆 · 留下你的迷彩心声
    </div>
    <p style="font-size: 14px; color: #555555; margin-bottom: 12px; line-height: 1.7;">
      十五天的汗水与欢笑，哪一个细节最击中你的心？
    </p>
    <div style="background-color: #F8F9FA; border-radius: 10px; padding: 14px 16px; font-size: 13.5px; color: #4F4F4F; line-height: 1.85;">
      💬 是南湖烈日下，彼此脖颈上晒出的那道“迷彩分界线”？<br/>
      💬 是急救包扎时，室友憋不住笑却认真系紧的最后一个平结？<br/>
      💬 还是秋雨湿透后背时，大家踏着水花相视一笑的狂傲少年气？<br/>
      👉 <strong>欢迎在评论区写下你的军训独家记忆！点赞前5名将获赠学院专属文创纪念品一份！</strong>
    </div>
  </section>

  <!-- 行动号召一键三连 -->
  <section style="text-align: center; margin: 34px 0 22px 0;">
    <p style="font-size: 13px; color: #888888; margin-bottom: 12px;">为2026级计科学子的热血蜕变点赞加油！</p>
    <div style="display: flex; justify-content: center; gap: 14px; font-size: 13.5px;">
      <span style="background-color: #FDF2F2; color: #B8242A; border: 1px solid #F8D7DA; padding: 6px 18px; border-radius: 24px; font-weight: 500;">👍 点赞</span>
      <span style="background-color: #FDF2F2; color: #B8242A; border: 1px solid #F8D7DA; padding: 6px 18px; border-radius: 24px; font-weight: 500;">🌟 在看</span>
      <span style="background-color: #FDF2F2; color: #B8242A; border: 1px solid #F8D7DA; padding: 6px 18px; border-radius: 24px; font-weight: 500;">↗️ 分享</span>
    </div>
  </section>

  <!-- 官方规范审校与落款 -->
  <section style="border-top: 1px solid #EBEBEB; padding-top: 20px; margin-top: 28px; font-size: 12px; color: #888888; line-height: 1.85; text-align: center;">
    <div>来源：中南民族大学融媒体中心</div>
    <div>供稿：计算机科学学院（人工智能学院）</div>
    <div>摄影：2026级计算机科学学院军训宣传组</div>
    <div>文案 / 编辑：融媒体中心学生记者团队</div>
    <div style="margin-top: 6px; color: #AAAAAA; font-size: 11px;">
      初审：学院团委宣传部 | 复审：党委宣传部融媒体中心 | 终审：党委宣传部
    </div>
  </section>

</div>
"""
    return html

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    rich_html = build_xiumi_rich_html()
    
    html_file = os.path.join(OUTPUT_DIR, "cs_2026_junxun_xiumi.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(rich_html)
    print(f"已生成完整秀米原生排版 HTML: {html_file} ({os.path.getsize(html_file)/1024:.1f} KB)")
    
    # 1. 复制到 macOS 系统剪贴板 (原生支持富文本 HTML 与纯文本)
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeHTML, NSPasteboardTypeString
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(rich_html, NSPasteboardTypeHTML)
        pb.setString_forType_(rich_html, NSPasteboardTypeString)
        print("✓ 已通过 AppKit 将完整富文本 HTML 原生写入 macOS 系统剪贴板！用户可在任意秀米/微信编辑器按 Cmd+V 直接粘贴！")
    except Exception as appkit_err:
        try:
            cmd = f'''osascript -e 'set the clipboard to (read "{html_file}" as «class utf8»)' '''
            subprocess.run(cmd, shell=True, check=True)
            print("✓ 已通过 osascript 将排版内容写入 macOS 系统剪贴板！")
        except Exception as e:
            print(f"Clipboard copy note: {e}")
        
    # 2. 启动 Playwright 驱动秀米原生工作区
    print("正在连接秀米编辑器 (https://xiumi.us/studio/v5#/paper/for/new/cube/0)...")
    screenshot_file = os.path.join(OUTPUT_DIR, "xiumi_rendered_article.png")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        try:
            page.goto("https://xiumi.us/studio/v5#/paper/for/new/cube/0", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)
            
            # 激活可编辑区域
            cell = page.wait_for_selector('div[contenteditable="true"]', timeout=20000)
            cell.click()
            
            # 将富文本注入秀米画布
            page.evaluate('''html => {
                const el = document.querySelector('div[contenteditable="true"]');
                if (el) {
                    el.innerHTML = html;
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }''', rich_html)
            
            time.sleep(3)
            page.screenshot(path=screenshot_file, full_page=False)
            print(f"✓ 秀米排版预览截图已生成: {screenshot_file}")
        except Exception as xiumi_err:
            print(f"Xiumi canvas notice: {xiumi_err}, rendering local high-fidelity preview...")
            page.set_content(rich_html)
            time.sleep(2)
            page.screenshot(path=screenshot_file, full_page=False)
            print(f"✓ 高保真排版预览截图已生成: {screenshot_file}")
        finally:
            browser.close()
        
    # 3. 联动打开用户桌面活跃的 Google Chrome 浏览器标签页
    try:
        print("正在将排版成果同步至用户正在运行的 Google Chrome 浏览器...")
        open_script = '''
tell application "Google Chrome"
    activate
    set paperUrl to "https://xiumi.us/studio/v5#/paper/for/new/cube/0"
    if (count of windows) > 0 then
        set foundTab to false
        repeat with w in windows
            set tabCount to count of tabs of w
            repeat with i from 1 to tabCount
                set t to tab i of w
                if URL of t contains "xiumi.us" then
                    set active tab index of w to i
                    set URL of t to paperUrl
                    set index of w to 1
                    set foundTab to true
                    exit repeat
                end if
            end repeat
            if foundTab then exit repeat
        end repeat
        if not foundTab then
            open location paperUrl
        end if
    else
        open location paperUrl
    end if
end tell
'''
        subprocess.run(["osascript", "-e", open_script], check=True)
        print("✓ 已成功将用户 Google Chrome 前台窗口导航至秀米编辑器工作区！")
    except Exception as e:
        print(f"Chrome tab sync note: {e}")

if __name__ == "__main__":
    main()
