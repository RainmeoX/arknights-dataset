"""
解析 PRTS Wiki 爬取的干员数据，提取完整字段
"""
import json
import re
import os

INPUT_FILE = "/home/z/my-project/download/arknights_dataset/all_operators.json"
OUTPUT_FILE = "/home/z/my-project/download/arknights_dataset/operators_parsed.json"


def clean_wikitext(text):
    """清理 wikitext 标记，返回纯文本"""
    if not text:
        return ""
    # 循环处理嵌套的 {{...}} 模板
    # 先处理简单的 color/修正/± 等
    for _ in range(5):  # 最多循环5次处理嵌套
        new_text = text
        # {{color|#XXX|内容}} -> 内容
        new_text = re.sub(r'\{\{color\|[^|]*\|([^{}]*)\}\}', r'\1', new_text)
        # {{*|XXX|内容}} -> 内容
        new_text = re.sub(r'\{\{\*[^|]*\|[^|]*\|([^{}]*)\}\}', r'\1', new_text)
        # {{修正|内容|...}} -> 内容
        new_text = re.sub(r'\{\{修正\|([^|}]*)\|[^{}]*\}\}', r'\1', new_text)
        # {{±|内容|...}} -> 内容
        new_text = re.sub(r'\{\{±\|([^|}]*)\|[^{}]*\}\}', r'\1', new_text)
        # {{xxx|内容}} 简单模板 -> 内容（只保留最后一个参数）
        new_text = re.sub(r'\{\{[^|}]*\|([^{|}]+)\}\}', r'\1', new_text)
        if new_text == text:
            break
        text = new_text
    
    # 移除 <br/> -> 换行
    text = text.replace('<br/>', '\n').replace('<br>', '\n')
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 移除剩余的 {{...}}
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    # 移除 [[...|...]] -> 后半部分
    text = re.sub(r'\[\[[^|]*\|([^\]]*)\]\]', r'\1', text)
    # 移除 [[...]] -> 内容
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    # 移除 ''' 和 ''
    text = text.replace("'''", '').replace("''", '')
    # 压缩空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_field(wikitext, field_name):
    """从 wikitext 中提取字段值 |字段名=值
    能处理值中包含 {{...}} 嵌套模板的情况
    """
    # 找到 |字段名= 的位置
    pattern = rf'\|{re.escape(field_name)}='
    match = re.search(pattern, wikitext)
    if not match:
        return ""
    
    start = match.end()
    # 从 start 开始，匹配到下一个顶层 | 或 }} 或换行
    # 需要处理 {{...}} 嵌套
    depth = 0
    i = start
    while i < len(wikitext):
        c = wikitext[i]
        if c == '{':
            depth += 1
        elif c == '}':
            if depth > 0:
                depth -= 1
            else:
                break
        elif c == '|' and depth == 0:
            break
        elif c == '\n' and depth == 0:
            break
        i += 1
    
    raw_value = wikitext[start:i].strip()
    return clean_wikitext(raw_value)


def extract_skills(wikitext):
    """提取技能信息
    技能格式：{{技能1 ... }} {{技能2 ... }} 等，每个块里有 |技能名=xxx
    """
    skills = []
    # 找所有 {{技能数字 或 {{技能 块
    # 用正则找 {{技能 后面跟数字或直接 |
    skill_blocks = []
    # 匹配 {{技能1, {{技能2, {{技能3 等
    for m in re.finditer(r'\{\{(技能\d*)\b', wikitext):
        block_start = m.start()
        # 找到匹配的 }}
        depth = 0
        i = block_start
        while i < len(wikitext):
            if wikitext[i] == '{':
                depth += 1
            elif wikitext[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = wikitext[block_start:i+2]
        skill_blocks.append(block)
    
    seen_names = set()
    for block in skill_blocks:
        name = extract_field(block, '技能名')
        if name and name not in seen_names:
            seen_names.add(name)
            # 找技能1描述（在块内）
            desc = extract_field(block, '技能1描述')
            if not desc:
                desc = extract_field(block, '技能描述')
            skills.append({'name': name, 'description': desc})
    
    return skills


def extract_talents(wikitext):
    """提取天赋信息"""
    talents = []
    # 找天赋（天赋1=名称, 天赋1条件=条件, 天赋1效果=效果）
    for i in range(1, 5):
        name = extract_field(wikitext, f'天赋{i}')
        cond = extract_field(wikitext, f'天赋{i}条件')
        effect = extract_field(wikitext, f'天赋{i}效果')
        if name and effect:
            talents.append({
                'name': name,
                'condition': cond,
                'effect': effect
            })
    return talents


def parse_operator(op):
    """解析单个干员"""
    raw = op.get('raw', '')
    
    # 稀有度转换：5=6星, 4=5星, 3=4星, 2=3星, 1=2星, 0=1星
    rarity_raw = extract_field(raw, '稀有度')
    rarity_map = {'5': '6星', '4': '5星', '3': '4星', '2': '3星', '1': '2星', '0': '1星'}
    rarity = rarity_map.get(rarity_raw, rarity_raw)
    
    info = {
        'name': op['name'],
        'profession': extract_field(raw, '职业'),
        'branch': extract_field(raw, '分支'),
        'rarity': rarity,
        'position': extract_field(raw, '位置'),
        'tags': extract_field(raw, '标签'),
        'feature': extract_field(raw, '特性'),
        'faction_country': extract_field(raw, '所属国家'),
        'faction_org': extract_field(raw, '所属组织'),
        'faction_team': extract_field(raw, '所属团队'),
        'obtain_method': extract_field(raw, '获得方式'),
        'illustrator': extract_field(raw, '画师'),
        'voice_cn': extract_field(raw, '中文配音'),
        'voice_jp': extract_field(raw, '日文配音'),
        'sub_type': extract_field(raw, '干员序号'),
        'talents': extract_talents(raw),
        'skills': extract_skills(raw),
    }
    
    # 属性
    info['hp_max'] = extract_field(raw, '精英2_满级_生命上限')
    info['atk_max'] = extract_field(raw, '精英2_满级_攻击')
    info['def_max'] = extract_field(raw, '精英2_满级_防御')
    info['res_max'] = extract_field(raw, '精英2_满级_法术抗性')
    info['cost'] = extract_field(raw, '部署费用')
    info['block_cnt'] = extract_field(raw, '阻挡数')
    info['attack_speed'] = extract_field(raw, '攻击速度')
    info['redeploy'] = extract_field(raw, '再部署')
    
    return info


def main():
    print("解析干员数据...")
    with open(INPUT_FILE, encoding='utf-8') as f:
        operators = json.load(f)
    
    parsed = []
    for op in operators:
        info = parse_operator(op)
        parsed.append(info)
    
    # 统计字段完整度
    print(f"\n总干员数: {len(parsed)}")
    fields = ['profession', 'rarity', 'branch', 'faction_country', 'faction_org', 
              'tags', 'feature', 'obtain_method', 'illustrator', 'voice_cn', 'voice_jp',
              'hp_max', 'atk_max', 'skills', 'talents']
    for field in fields:
        count = sum(1 for op in parsed if op.get(field))
        print(f"  {field}: {count}/{len(parsed)} ({count/len(parsed)*100:.1f}%)")
    
    # 保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(parsed, f, ensure_ascii=False, indent=2)
    
    print(f"\n解析完成，保存到: {OUTPUT_FILE}")
    
    # 打印示例
    print("\n=== 示例：银灰 ===")
    for op in parsed:
        if op['name'] == '银灰':
            for k, v in op.items():
                print(f"  {k}: {str(v)[:120]}")
            break


if __name__ == "__main__":
    main()
