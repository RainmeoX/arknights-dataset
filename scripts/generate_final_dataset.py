"""
整合所有数据，生成最终的明日方舟微调数据集
- 干员基础信息问答
- 语音台词（人设对话）
- 综合问答
"""
import json
import random
import os

random.seed(42)

DATA_DIR = "/home/z/my-project/download/arknights_dataset"

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), encoding='utf-8') as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("生成最终微调数据集")
    print("=" * 60)
    
    operators = load_json("operators_parsed.json")
    voices = load_json("operator_voices.json")
    
    # 建立语音索引
    voice_map = {v['name']: v['voices'] for v in voices}
    
    all_data = []
    
    # ========== 1. 基础信息问答 ==========
    print("\n[1/3] 生成基础信息问答...")
    for op in operators:
        name = op.get('name', '')
        if not name:
            continue
        
        profession = op.get('profession', '')
        branch = op.get('branch', '')
        rarity = op.get('rarity', '')
        position = op.get('position', '')
        tags = op.get('tags', '')
        feature = op.get('feature', '')
        faction_country = op.get('faction_country', '')
        faction_org = op.get('faction_org', '')
        obtain_method = op.get('obtain_method', '')
        illustrator = op.get('illustrator', '')
        voice_cn = op.get('voice_cn', '')
        hp_max = op.get('hp_max', '')
        atk_max = op.get('atk_max', '')
        def_max = op.get('def_max', '')
        res_max = op.get('res_max', '')
        cost = op.get('cost', '')
        block_cnt = op.get('block_cnt', '')
        skills = op.get('skills', [])
        talents = op.get('talents', [])
        
        # 职业信息
        if profession and rarity:
            all_data.append({
                "instruction": f"{name}是什么职业的干员？",
                "output": f"{name}是{rarity}{profession}干员，分支为{branch}。"
            })
        
        # 星级
        if rarity:
            all_data.append({
                "instruction": f"{name}是几星干员？",
                "output": f"{name}是{rarity}干员。"
            })
        
        # 特性
        if feature:
            all_data.append({
                "instruction": f"{name}的特性是什么？",
                "output": f"{name}的特性：{feature}"
            })
        
        # 阵营
        if faction_country or faction_org:
            faction = "、".join(filter(None, [faction_country, faction_org]))
            all_data.append({
                "instruction": f"{name}属于哪个阵营？",
                "output": f"{name}属于{faction}。"
            })
        
        # 标签
        if tags:
            all_data.append({
                "instruction": f"{name}有什么标签？",
                "output": f"{name}的标签：{tags}。"
            })
        
        # 获取方式
        if obtain_method:
            all_data.append({
                "instruction": f"怎么获得{name}？",
                "output": f"{name}的获得方式：{obtain_method}。"
            })
        
        # 画师
        if illustrator:
            all_data.append({
                "instruction": f"{name}的画师是谁？",
                "output": f"{name}的画师是{illustrator}。"
            })
        
        # 中文配音
        if voice_cn:
            all_data.append({
                "instruction": f"{name}的中文配音是谁？",
                "output": f"{name}的中文配音是{voice_cn}。"
            })
        
        # 满级属性
        if hp_max and atk_max:
            props = f"生命上限：{hp_max}，攻击：{atk_max}"
            if def_max: props += f"，防御：{def_max}"
            if res_max: props += f"，法术抗性：{res_max}"
            if cost: props += f"，部署费用：{cost}"
            if block_cnt: props += f"，阻挡数：{block_cnt}"
            all_data.append({
                "instruction": f"{name}的满级属性是多少？",
                "output": f"{name}精英2满级属性：{props}。"
            })
        
        # 技能
        for skill in skills:
            sname = skill.get('name', '')
            sdesc = skill.get('description', '')
            if sname:
                output = f"{name}的技能「{sname}」"
                if sdesc:
                    output += f"：{sdesc}"
                all_data.append({
                    "instruction": f"{name}的技能{sname}有什么效果？",
                    "output": output
                })
        
        # 天赋
        for talent in talents:
            tname = talent.get('name', '')
            tcond = talent.get('condition', '')
            teffect = talent.get('effect', '')
            if tname and teffect:
                output = f"{name}的天赋「{tname}」"
                if tcond: output += f"（{tcond}）"
                output += f"：{teffect}"
                all_data.append({
                    "instruction": f"{name}的天赋是什么？",
                    "output": output
                })
    
    print(f"  基础信息问答: {len(all_data)} 条")
    base_count = len(all_data)
    
    # ========== 2. 语音台词（人设对话）==========
    print("\n[2/3] 生成语音台词数据...")
    voice_count = 0
    for name, voice_list in voice_map.items():
        for v in voice_list:
            scene = v.get('scene', '')
            text = v.get('text', '')
            if scene and text:
                # 把语音台词转成对话格式
                all_data.append({
                    "instruction": f"扮演{name}，说一句{scene}的台词",
                    "output": text
                })
                voice_count += 1
    print(f"  语音台词: {voice_count} 条")
    
    # ========== 3. 综合问答 ==========
    print("\n[3/3] 生成综合问答...")
    comp_count = 0
    for op in operators:
        name = op.get('name', '')
        if not name: continue
        profession = op.get('profession', '')
        rarity = op.get('rarity', '')
        branch = op.get('branch', '')
        feature = op.get('feature', '')
        skills = op.get('skills', [])
        
        # 综合介绍
        intro = f"{name}是{rarity}{profession}干员"
        if branch: intro += f"（{branch}）"
        if feature: intro += f"，特性为{feature}"
        if skills:
            skill_names = [s['name'] for s in skills if s.get('name')]
            if skill_names:
                intro += f"，技能包括{'、'.join(skill_names)}"
        intro += "。"
        
        all_data.append({
            "instruction": f"介绍一下{name}这个干员",
            "output": intro
        })
        comp_count += 1
    print(f"  综合问答: {comp_count} 条")
    
    # ========== 打乱并保存 ==========
    random.shuffle(all_data)
    
    print(f"\n{'='*60}")
    print(f"数据集统计:")
    print(f"  总问答对: {len(all_data)}")
    print(f"  - 基础信息: {base_count}")
    print(f"  - 语音台词: {voice_count}")
    print(f"  - 综合问答: {comp_count}")
    print(f"{'='*60}")
    
    # 保存为 JSONL（instruction/output 格式）
    jsonl_file = os.path.join(DATA_DIR, "arknights_finetune_dataset.jsonl")
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for item in all_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # 保存为 ChatML 格式
    chatml_data = []
    for item in all_data:
        chatml_data.append({
            "messages": [
                {"role": "system", "content": "你是明日方舟游戏助手，可以回答关于干员的各种问题，也能扮演干员进行对话。"},
                {"role": "user", "content": item["instruction"]},
                {"role": "assistant", "content": item["output"]}
            ]
        })
    
    chatml_file = os.path.join(DATA_DIR, "arknights_finetune_chatml.json")
    with open(chatml_file, 'w', encoding='utf-8') as f:
        json.dump(chatml_data, f, ensure_ascii=False, indent=2)
    
    # 划分训练集/验证集（9:1）
    split_idx = int(len(all_data) * 0.9)
    train_data = all_data[:split_idx]
    val_data = all_data[split_idx:]
    
    train_file = os.path.join(DATA_DIR, "train.jsonl")
    val_file = os.path.join(DATA_DIR, "val.jsonl")
    with open(train_file, 'w', encoding='utf-8') as f:
        for item in train_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    with open(val_file, 'w', encoding='utf-8') as f:
        for item in val_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"\n数据集已保存:")
    print(f"  - arknights_finetune_dataset.jsonl ({len(all_data)} 条，完整)")
    print(f"  - arknights_finetune_chatml.json ({len(all_data)} 条，ChatML格式)")
    print(f"  - train.jsonl ({len(train_data)} 条，训练集)")
    print(f"  - val.jsonl ({len(val_data)} 条，验证集)")
    
    # 示例
    print(f"\n=== 示例问答 ===")
    for item in all_data[:5]:
        print(f"Q: {item['instruction']}")
        print(f"A: {item['output'][:100]}")
        print()


if __name__ == "__main__":
    main()
