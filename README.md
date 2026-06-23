# Arknights Dataset for LLM Fine-tuning

> 明日方舟干员数据集 - 用于大模型微调的问答对数据

## 📊 数据集概览

| 项目 | 数量 |
|:---|:---:|
| 干员总数 | 449 |
| 基础信息问答 | 6,314 条 |
| 语音台词（人设对话） | 15,858 条 |
| 综合问答 | 449 条 |
| **总问答对** | **22,621 条** |
| 训练集 | 20,358 条（90%） |
| 验证集 | 2,263 条（10%） |

## 📁 目录结构

```
arknights-dataset/
├── data/                           # 微调数据集
│   ├── train.jsonl                 # 训练集（20,358 条）
│   ├── val.jsonl                   # 验证集（2,263 条）
│   ├── arknights_finetune_dataset.jsonl   # 完整数据集（22,621 条）
│   ├── arknights_finetune_chatml.json     # ChatML 格式
│   └── dataset_stats.json          # 数据统计
├── raw/                            # 原始爬取数据
│   ├── operators_parsed.json       # 干员结构化数据（449 个）
│   ├── operator_voices.json        # 语音台词（425 个干员）
│   ├── all_operators.json          # 原始 wikitext
│   └── operator_list.json          # 干员名列表
├── scripts/                        # 爬取与处理脚本
│   ├── crawl_arknights.py          # 干员数据爬取（多线程）
│   ├── parse_arknights.py          # wikitext 解析
│   ├── crawl_voices.py             # 语音台词爬取
│   └── generate_final_dataset.py   # 生成微调数据集
├── examples/                       # 示例数据
│   └── sample_qa.json              # 20 条示例问答
├── LICENSE
└── README.md
```

## 📝 数据格式

### JSONL 格式（train.jsonl / val.jsonl）

每行一个 JSON 对象，包含 `instruction`（问题）和 `output`（回答）：

```json
{
  "instruction": "银灰是什么职业的干员？",
  "output": "银灰是6星近卫干员，分支为领主。"
}
```

### ChatML 格式（arknights_finetune_chatml.json）

```json
{
  "messages": [
    {"role": "system", "content": "你是明日方舟游戏助手，可以回答关于干员的各种问题，也能扮演干员进行对话。"},
    {"role": "user", "content": "银灰是什么职业的干员？"},
    {"role": "assistant", "content": "银灰是6星近卫干员，分支为领主。"}
  ]
}
```

## 🎯 数据类型

### 1. 基础信息问答（6,314 条）

涵盖干员的各类属性查询：

- 职业与分支：`银灰是什么职业的干员？`
- 星级：`阿米娅是几星干员？`
- 阵营：`银灰属于哪个阵营？`
- 属性：`星熊的满级属性是多少？`
- 技能：`银灰有哪些技能？`
- 天赋：`银灰的天赋是什么？`
- 获得方式：`能天使怎么获得？`
- 画师/配音：`银灰的画师是谁？`

### 2. 语音台词（15,858 条）

干员人设对话，可用于角色扮演微调：

- 任命助理：`扮演银灰，说一句任命助理的台词`
- 交谈：`扮演阿米娅，说一句交谈1的台词`
- 战斗：`扮演陈，说一句战斗开始的台词`
- 信赖触摸：`扮演能天使，说一句信赖触摸的台词`
- 精英化晋升：`扮演银灰，说一句精英化晋升2的台词`

### 3. 综合问答（449 条）

干员完整介绍：

- `介绍一下银灰这名干员`
- `说说阿米娅的特点`

## 📊 干员分布

### 按星级

| 星级 | 数量 |
|:---:|:---:|
| 6星 | 141 |
| 5星 | 200 |
| 4星 | 70 |
| 3星 | 22 |
| 2星 | 5 |
| 1星 | 11 |

### 按职业

| 职业 | 数量 |
|:---:|:---:|
| 近卫 | 88 |
| 术师 | 62 |
| 狙击 | 62 |
| 特种 | 50 |
| 重装 | 50 |
| 辅助 | 49 |
| 先锋 | 45 |
| 医疗 | 43 |

## 🔧 数据来源

数据爬取自 [PRTS Wiki](https://prts.wiki/)（明日方舟中文 Wiki），使用 MediaWiki API 获取。

### 爬取流程

1. **获取干员列表**：通过 `Category:干员` 获取全部 449 个干员
2. **爬取干员页面**：多线程（8线程）爬取每个干员的 wikitext，耗时约 14 秒
3. **解析结构化数据**：提取职业、星级、属性、技能、天赋等字段
4. **爬取语音台词**：爬取 `干员名/语音记录` 子页面，提取中文台词
5. **生成问答对**：基于结构化数据生成多类型问答对

### 重新爬取

```bash
# 安装依赖
pip install requests

# 运行爬取脚本
python scripts/crawl_arknights.py      # 爬取干员基础数据
python scripts/parse_arknights.py      # 解析结构化数据
python scripts/crawl_voices.py         # 爬取语音台词
python scripts/generate_final_dataset.py  # 生成微调数据集
```

## 🚀 使用方法

### 用于 LoRA 微调

数据集兼容主流微调框架（TRL / LLaMA-Factory / Axolotl 等）：

```python
from datasets import load_dataset

# 加载训练集
dataset = load_dataset("json", data_files="data/train.jsonl")
```

### 数据字段说明

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `instruction` | string | 用户问题/指令 |
| `output` | string | 模型回答 |

ChatML 格式额外包含 `messages` 字段，适合对话模型微调。

## 📈 训练后能力

基于此数据集微调后，模型可获得以下能力：

- ✅ **干员知识问答**：回答干员的职业、星级、属性、技能等问题
- ✅ **角色扮演**：扮演干员用其语气说话
- ✅ **干员推荐**：根据需求推荐合适干员
- ✅ **阵营/职业查询**：按阵营或职业筛选干员
- ✅ **技能/天赋查询**：查询干员的技能和天赋详情

## ⚠️ 注意事项

- 数据爬取自 PRTS Wiki，仅供学习研究使用
- 游戏内容版权归鹰角网络所有
- 如需用于商业用途，请先获得相应授权

## 📄 License

MIT License
