# SCMU WeChat Skill ｜ 中南民族大学官方微信公众号推文助手

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-green.svg)](scripts/check_compliance.py)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/xiangbianpangde/scmu-wechat-skill/pulls)

专为**中南民族大学**（South-Central Minzu University, SCMU）官方微信公众号设计的高能 AI Agent 创作与审校技能库。深度融合民大校情校史、标志性校园意象、视觉识别规范与国家民委高校“三审三校”政治把关要求，配套离线自动化合规质检脚本，打造全流程高质量校园推文生产力体系。

---

## 🌟 核心特色

- 🏛️ **深度嵌入民大校本知识**：内置建校历史、南区双塔、南湖风物、石榴园/石榴籽广场、民族学博物馆、20个教学科研单位官方全称及校训（笃信好学，自然宽和）。
- 🛡️ **严格把关“三审三校”政治红线**：紧紧围绕“铸牢中华民族共同体意识”主线，严格执行高校“教育与宗教相分离”原则与涉民族规范用语体系。
- 📑 **四大核心特色栏目矩阵**：
  - **【民大要闻】**：重大战略会议、上级调研考察、科研重大突破公文式通稿。
  - **【青春民大】**：国奖学霸、科创先锋、支教榜样、名师专访生动人物报道。
  - **【风物民大】**：二十四节气、双塔暮色、南湖晨光、银杏季、毕业季情怀美学散文。
  - **【服务民大】**：迎新报到、选课考试、放假返校、掌上校园后勤实用办事指南。
- 🎨 **官方专属视觉配色规范**：集成民大石榴红（`#B8242A`）、南湖碧波蓝（`#1F5F8B`）、晨曦暖阳金（`#D4A359`）代码与微信排版 HTML 样式卡片。
- 🚀 **配套离线 Python 质检工具**：纯标准库零依赖脚本（`check_compliance.py`），毫秒级拦截敏感词、宗教泛化、曾用名误用与校训地标笔误。

---

## 📂 项目结构

```text
scmu-wechat-skill/
├── SKILL.md                          # Agent Skill 核心规范与工作流入口
├── README.md                         # 项目中文详细说明文档
├── LICENSE                           # MIT 开源协议
├── .gitignore                        # Git 忽略配置
├── references/                       # 结构化参考规范库
│   ├── scmu_profile.md               # 民大校情概况、地标文化、学院简称与视觉色彩体系
│   ├── compliance_guide.md           # 铸牢中华民族共同体意识主线、民族宗教红线与审校指南
│   └── templates.md                  # 五大标题生成公式、四大栏目模板及微信排版组件
├── scripts/                          # 自动化工具链
│   ├── check_compliance.py           # 离线三审三校自动化合规质检脚本（纯标准库）
│   └── tests/
│       └── test_compliance.py       # 单元测试用例
└── examples/
    └── sample_draft.md               # 标准样例推文（【青春民大】国奖学霸专访）
```

---

## 🛠️ 快速上手

### 1. 作为 Agent Skill 使用（支持 Antigravity / Claude Code / Cursor 等）

#### 在 Antigravity 中全局加载
直接建立软链接至全局技能目录：
```bash
ln -s /path/to/scmu-wechat-skill ~/.gemini/config/skills/scmu-wechat
```
在任何对话中输入指令即可唤醒：
> *“请用中南民大公众号风格，写一篇关于双塔秋日风光与银杏节气的推文。”*
> *“帮我审校这篇民大新闻稿，检查领导职务排序与涉民族用语合规性。”*

---

### 2. 独立运行 Python 质检脚本

本脚本无需安装任何第三方库（基于 Python 3 标准库构建）：

```bash
# 检查指定推文文件
python3 scripts/check_compliance.py examples/sample_draft.md

# 严格模式：发现 WARNING 级别问题时也返回非 0 退出码（适合 CI/CD 流程）
python3 scripts/check_compliance.py your_draft.md --strict

# 输出结构化 JSON 格式数据
python3 scripts/check_compliance.py your_draft.md --json

# 支持管道输入
cat your_draft.md | python3 scripts/check_compliance.py -
```

#### 质检脚本检测等级说明

| 等级 | 标识 | 严重程度 | 说明 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| **阻断项** | `BLOCKER` | ❌ 严禁发布 | 违背民族宗教政策、主线表述错误 | “铸造共同体意识”（错字）、宗教进校园宣传 |
| **警告项** | `WARNING` | ⚠️ 建议修正 | 校名校训笔误、历史旧称误用、地标错写 | “中南民院”（旧称）、“自然和谐”（校训笔误）、“民俗博物馆”（漏字） |
| **建议项** | `SUGGESTION` | 💡 排版优化 | 微信排版规范、标点符号、缺少官方融媒体落款 | 一级标题带句号、长篇推文无配图占位 |

---

## 🧪 运行测试用例

```bash
python3 scripts/tests/test_compliance.py
```

---

## 🎨 视觉色彩指引

在排版与图文设计时推荐选用民大专属品牌色彩：

| 色彩名称 | 色值代码 | 推荐应用场景 |
| :--- | :--- | :--- |
| **民大石榴红** | `#B8242A` | 一级大标题、重点加粗强调、官方重要喜报、边框标记 |
| **南湖碧波蓝** | `#1F5F8B` | 湖水意象段落、学术要闻卡片底衬、引言左边框 |
| **晨曦暖阳金** | `#D4A359` | 获奖荣誉高亮、名片标签、星级提示、重点数字 |
| **水墨深灰**   | `#2D3142` | 正文阅读文本，温和护眼 |
| **素净浅灰**   | `#F8F9FA` | 引用框底色、代码块底衬 |

---

## 🤝 贡献指南

欢迎民大师生、校友与新媒体运营同仁共同完善本项目：
1. 提交 Issue 反馈校园最新常用地标、学院调整或新增易错词。
2. 提交 Pull Request 丰富栏目模版与生图提示词库。

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 授权开源。
