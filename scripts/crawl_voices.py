"""
爬取干员语音台词数据
"""
import requests
import json
import time
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

BASE_URL = "https://prts.wiki/api.php"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUTPUT_DIR = "/home/z/my-project/download/arknights_dataset"
VOICE_DIR = os.path.join(OUTPUT_DIR, "voices")
os.makedirs(VOICE_DIR, exist_ok=True)

MAX_WORKERS = 8
stats_lock = Lock()
stats = {"success": 0, "fail": 0, "total": 0}


def get_page_content(title):
    params = {
        "action": "query", "titles": title,
        "prop": "revisions", "rvprop": "content",
        "format": "json", "rvlimit": 1
    }
    for attempt in range(3):
        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for pid, page in pages.items():
                revisions = page.get("revisions", [])
                if revisions:
                    return revisions[0].get("*", "")
            return None
        except:
            if attempt == 2: return None
            time.sleep(1)


def clean_wikitext(text):
    if not text: return ""
    for _ in range(5):
        new_text = text
        new_text = re.sub(r'\{\{color\|[^|]*\|([^{}]*)\}\}', r'\1', new_text)
        new_text = re.sub(r'\{\{[^|}]*\|([^{|}]+)\}\}', r'\1', new_text)
        if new_text == text: break
        text = new_text
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    text = re.sub(r'\[\[[^|]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    text = text.replace("'''", '').replace("''", '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_voices(wikitext):
    """提取语音台词
    格式：|标题1=xxx |台词1={{VoiceData/word|中文|内容}}...
    """
    voices = []
    # 找所有 |标题N=xxx
    title_matches = re.findall(r'\|标题(\d+)=([^\n|]+)', wikitext)
    for num, title in title_matches:
        title = clean_wikitext(title.strip())
        if not title:
            continue
        # 找对应的 |台词N= 内容，提取中文部分
        # 格式：|台词1={{VoiceData/word|中文|内容}}{{VoiceData/word|日文|...}}...
        line_pattern = rf'\|台词{num}='
        line_match = re.search(line_pattern, wikitext)
        if not line_match:
            continue
        
        start = line_match.end()
        # 找到下一个 |标题 或 |语音 或 }}
        end = start
        depth = 0
        while end < len(wikitext):
            c = wikitext[end]
            if c == '{': depth += 1
            elif c == '}':
                if depth > 0: depth -= 1
            elif c == '|' and depth == 0:
                break
            elif c == '\n' and depth == 0:
                break
            end += 1
        
        line_content = wikitext[start:end]
        # 提取中文台词：{{VoiceData/word|中文|内容}}
        cn_match = re.search(r'\{\{VoiceData/word\|中文\|([^}]*)\}\}', line_content)
        if cn_match:
            content = clean_wikitext(cn_match.group(1).strip())
            if content:
                voices.append({"scene": title, "text": content})
    
    return voices


def crawl_voice(operator):
    title = f"{operator}/语音记录"
    raw = get_page_content(title)
    if not raw:
        with stats_lock:
            stats["fail"] += 1
        return None
    
    voices = extract_voices(raw)
    if not voices:
        with stats_lock:
            stats["fail"] += 1
        return None
    
    with stats_lock:
        stats["success"] += 1
    
    # 保存单独文件
    safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', operator)
    with open(os.path.join(VOICE_DIR, f"{safe_name}.json"), 'w', encoding='utf-8') as f:
        json.dump({"name": operator, "voices": voices}, f, ensure_ascii=False, indent=2)
    
    return {"name": operator, "voices": voices}


def main():
    print("=" * 60)
    print("爬取干员语音台词数据")
    print("=" * 60)
    
    with open(os.path.join(OUTPUT_DIR, "operator_list.json"), encoding='utf-8') as f:
        operators = json.load(f)
    
    stats["total"] = len(operators)
    print(f"共 {len(operators)} 个干员")
    
    print(f"\n开始多线程爬取（{MAX_WORKERS} 线程）...")
    start_time = time.time()
    
    all_voices = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(crawl_voice, op): op for op in operators}
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                all_voices.append(result)
            if i % 50 == 0:
                print(f"  进度: {i}/{stats['total']}, 成功: {stats['success']}, 失败: {stats['fail']}")
    
    elapsed = time.time() - start_time
    print(f"\n爬取完成！耗时 {elapsed:.1f} 秒")
    print(f"成功: {stats['success']}, 失败: {stats['fail']}")
    
    # 统计语音条数
    total_voices = sum(len(v['voices']) for v in all_voices)
    print(f"语音台词总数: {total_voices}")
    
    # 保存
    output_file = os.path.join(OUTPUT_DIR, "operator_voices.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_voices, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {output_file}")
    
    # 示例
    if all_voices:
        print(f"\n=== 示例：{all_voices[0]['name']} 的语音 ===")
        for v in all_voices[0]['voices'][:3]:
            print(f"  [{v['scene']}] {v['text'][:80]}")


if __name__ == "__main__":
    main()
