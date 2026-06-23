"""
明日方舟助手评估测试集
- test_knowledge.json: 100道知识问答（有标准答案关键词）
- test_roleplay.json: 50道角色扮演（有真实台词参考）
- test_hallucination.json: 30道幻觉检测（问不存在的干员）
"""
import json
import random
import os

random.seed(42)

DATA_DIR = "/home/z/my-project/download/arknights_dataset"
OUTPUT_DIR = "/home/z/my-project/download/arknights_eval"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 加载干员数据
with open(f"{DATA_DIR}/operators_parsed.json", encoding="utf-8") as f:
    operators = json.load(f)

with open(f"{DATA_DIR}/operator_voices.json", encoding="utf-8") as f:
    voices = json.load(f)

voice_map = {v["name"]: v["voices"] for v in voices}


# ========== 1. 知识问答测试集（100题）==========
def generate_knowledge_test():
    """生成100道知识问答，每题有标准答案关键词"""
    tests = []
    
    # 按职业分组
    by_profession = {}
    for op in operators:
        prof = op.get("profession", "")
        if prof:
            by_profession.setdefault(prof, []).append(op)
    
    # 题型1：问职业（30题）
    sample_ops = random.sample(operators, min(30, len(operators)))
    for op in sample_ops:
        name = op["name"]
        profession = op.get("profession", "")
        branch = op.get("branch", "")
        rarity = op.get("rarity", "")
        if profession:
            tests.append({
                "id": f"K{len(tests)+1:03d}",
                "type": "profession",
                "question": f"{name}是什么职业的干员？",
                "keywords": [profession, rarity.replace("星", "") + "星"],
                "standard_answer": f"{name}是{rarity}{profession}干员，分支为{branch}。"
            })
    
    # 题型2：问星级（20题）
    sample_ops = random.sample(operators, min(20, len(operators)))
    for op in sample_ops:
        name = op["name"]
        rarity = op.get("rarity", "")
        if rarity:
            tests.append({
                "id": f"K{len(tests)+1:03d}",
                "type": "rarity",
                "question": f"{name}是几星干员？",
                "keywords": [rarity, rarity.replace("星", "")],
                "standard_answer": f"{name}是{rarity}干员。"
            })
    
    # 题型3：问阵营（15题）
    ops_with_faction = [op for op in operators if op.get("faction_country")]
    sample_ops = random.sample(ops_with_faction, min(15, len(ops_with_faction)))
    for op in sample_ops:
        name = op["name"]
        faction = op.get("faction_country", "")
        if faction:
            tests.append({
                "id": f"K{len(tests)+1:03d}",
                "type": "faction",
                "question": f"{name}属于哪个阵营？",
                "keywords": [faction],
                "standard_answer": f"{name}属于{faction}阵营。"
            })
    
    # 题型4：问技能（20题）
    ops_with_skills = [op for op in operators if op.get("skills")]
    sample_ops = random.sample(ops_with_skills, min(20, len(ops_with_skills)))
    for op in sample_ops:
        name = op["name"]
        skills = op.get("skills", [])
        if skills:
            skill_names = [s["name"] for s in skills]
            tests.append({
                "id": f"K{len(tests)+1:03d}",
                "type": "skills",
                "question": f"{name}有哪些技能？",
                "keywords": skill_names,
                "standard_answer": f"{name}的技能有：{'、'.join(skill_names)}。"
            })
    
    # 题型5：问属性（15题）
    ops_with_stats = [op for op in operators if op.get("hp_max")]
    sample_ops = random.sample(ops_with_stats, min(15, len(ops_with_stats)))
    for op in sample_ops:
        name = op["name"]
        hp = op.get("hp_max", "")
        atk = op.get("atk_max", "")
        if hp and atk:
            tests.append({
                "id": f"K{len(tests)+1:03d}",
                "type": "stats",
                "question": f"{name}的满级生命值和攻击力是多少？",
                "keywords": [str(hp), str(atk)],
                "standard_answer": f"{name}精英2满级：生命上限{hp}，攻击{atk}。"
            })
    
    return tests[:100]


# ========== 2. 角色扮演测试集（50题）==========
def generate_roleplay_test():
    """生成50道角色扮演题，有真实台词参考"""
    tests = []
    
    # 选有语音的干员
    ops_with_voices = [name for name in voice_map.keys() if voice_map[name]]
    sample_names = random.sample(ops_with_voices, min(50, len(ops_with_voices)))
    
    for name in sample_names:
        voices_list = voice_map[name]
        if not voices_list:
            continue
        # 随机选一条语音
        voice = random.choice(voices_list)
        scene = voice["scene"]
        text = voice["text"]
        
        tests.append({
            "id": f"R{len(tests)+1:03d}",
            "type": "roleplay",
            "question": f"扮演{name}，说一句{scene}的台词",
            "reference": text,
            "operator": name,
            "scene": scene
        })
    
    return tests[:50]


# ========== 3. 幻觉检测测试集（30题）==========
def generate_hallucination_test():
    """生成30道幻觉检测题，问不存在的干员"""
    tests = []
    
    # 编造不存在的干员名
    fake_names = [
        "张三", "李四", "王五", "赵六", "钱七",
        "孙八", "周九", "吴十", "郑十一", "王十二",
        "李白", "杜甫", "苏轼", "辛弃疾", "李清照",
        "诸葛亮", "司马懿", "周瑜", "陆逊", "吕蒙",
        "亚瑟", "梅林", "兰斯洛特", "高文", "加拉哈德",
        "桃太郎", "金太郎", "浦岛太郎", "一寸法师", "竹取公主"
    ]
    
    for name in fake_names[:30]:
        question_type = random.choice(["profession", "skill", "faction"])
        if question_type == "profession":
            q = f"{name}是什么职业的干员？"
        elif question_type == "skill":
            q = f"{name}的技能是什么？"
        else:
            q = f"{name}属于哪个阵营？"
        
        tests.append({
            "id": f"H{len(tests)+1:03d}",
            "type": "hallucination",
            "question": q,
            "expected_behavior": "拒绝回答或说明不认识该干员",
            "keywords_reject": ["不认识", "不知道", "不存在", "没有", "未找到", "不了解", "没有这位"],
            "fake_name": name
        })
    
    return tests


# ========== 生成所有测试集 ==========
print("生成评估测试集...")

knowledge_tests = generate_knowledge_test()
roleplay_tests = generate_roleplay_test()
hallucination_tests = generate_hallucination_test()

# 保存
with open(f"{OUTPUT_DIR}/test_knowledge.json", "w", encoding="utf-8") as f:
    json.dump(knowledge_tests, f, ensure_ascii=False, indent=2)

with open(f"{OUTPUT_DIR}/test_roleplay.json", "w", encoding="utf-8") as f:
    json.dump(roleplay_tests, f, ensure_ascii=False, indent=2)

with open(f"{OUTPUT_DIR}/test_hallucination.json", "w", encoding="utf-8") as f:
    json.dump(hallucination_tests, f, ensure_ascii=False, indent=2)

print(f"知识问答测试集: {len(knowledge_tests)} 题 → test_knowledge.json")
print(f"角色扮演测试集: {len(roleplay_tests)} 题 → test_roleplay.json")
print(f"幻觉检测测试集: {len(hallucination_tests)} 题 → test_hallucination.json")

# 示例
print("\n=== 知识问答示例 ===")
for t in knowledge_tests[:3]:
    print(f"Q: {t['question']}")
    print(f"关键词: {t['keywords']}")
    print(f"标准答案: {t['standard_answer']}")
    print()

print("=== 角色扮演示例 ===")
for t in roleplay_tests[:3]:
    print(f"Q: {t['question']}")
    print(f"参考台词: {t['reference'][:80]}")
    print()

print("=== 幻觉检测示例 ===")
for t in hallucination_tests[:3]:
    print(f"Q: {t['question']}")
    print(f"期望: {t['expected_behavior']}")
    print()
