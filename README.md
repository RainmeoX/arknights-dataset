# Arknights Dataset

明日方舟干员数据集，用于大模型微调的问答对数据。

## 项目背景

为了给明日方舟角色助手（[arknights-qwen-assistant](https://github.com/RainmeoX/arknights-qwen-assistant)）准备训练数据，我爬取并整理了干员的结构化资料和语音台词，生成可直接用于微调的问答对。

## 数据规模

- 干员总数：449
- 基础信息问答：6,314 条
- 语音台词（人设对话）：15,858 条
- 综合问答：449 条
- 总问答对：22,621 条（训练 20,358 / 验证 2,263）

## 数据格式

JSONL（`train.jsonl` / `val.jsonl`），每行一个对象：

```json
{
  "instruction": "银灰是什么职业的干员？",
  "output": "银灰是6星近卫干员，分支为领主。"
}
```

另提供 ChatML 格式（`arknights_finetune_chatml.json`）用于对话模型微调。

## 数据来源

[PRTS Wiki](https://prts.wiki/)（明日方舟中文 Wiki），通过 MediaWiki API 获取，多线程（8 线程）爬取。

## 我的工作

- 写爬取脚本（`crawl_arknights.py` 等）
- 解析 wikitext 提取结构化字段（职业 / 星级 / 属性 / 技能 / 天赋）
- 爬取并整理语音台词
- 生成多类型问答对

## 遇到的问题

- 部分子页面结构不一致，需要针对性解析
- 语音台词页面需要单独爬取，字段格式不统一

## 使用方式

```python
from datasets import load_dataset
dataset = load_dataset("json", data_files="data/train.jsonl")
```

数据集兼容 TRL / LLaMA-Factory / Axolotl 等主流微调框架。

## 项目不足

- 数据来自单一 Wiki，可能有滞后 / 偏差
- 未做严格人工校验
- 语音台词偏"人设对话"，推理类问答较少

## 后续计划

- 补充更多干员动态信息
- 增加角色扮演数据集规模
- 做一轮人工抽检

## Reflection

这是我从"用现成数据"到"自己造数据"的第一步，也让我理解了数据质量直接决定下游模型的上限——模型再好，喂进去的是噪声也出不来好结果。

## License

MIT
