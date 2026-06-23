"""
PRTS Wiki 明日方舟干员数据多线程爬取
- 使用 MediaWiki API 获取干员列表
- 多线程爬取每个干员的详细信息
- 生成问答对格式的微调数据集
"""
import requests
import json
import time
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ========== 配置 ==========
BASE_URL = "https://prts.wiki/api.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
OUTPUT_DIR = "/home/z/my-project/download/arknights_dataset"
RAW_DIR = os.path.join(OUTPUT_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 多线程配置
MAX_WORKERS = 8          # 并发线程数
REQUEST_TIMEOUT = 30     # 请求超时秒数
RETRY_TIMES = 3          # 重试次数

# 统计锁
stats_lock = Lock()
stats = {"success": 0, "fail": 0, "total": 0}


def get_operator_list():
    """获取所有干员名称列表"""
    print("正在获取干员列表...")
    operators = []
    cmcontinue = None
    
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:干员",
            "cmlimit": 500,
            "format": "json"
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        
        resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        
        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            title = m.get("title", "")
            # 过滤掉子页面和特殊页面，只保留干员名
            if "/" not in title and not title.startswith("PRTS:") and not title.startswith("分类:"):
                operators.append(title)
        
        if "continue" in data:
            cmcontinue = data["continue"].get("cmcontinue")
        else:
            break
    
    # 去重
    operators = list(dict.fromkeys(operators))
    print(f"共获取 {len(operators)} 个干员")
    return operators


def get_page_content(title):
    """获取页面原始 wikitext 内容"""
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "titles": title,
        "format": "json",
        "formatversion": "2"
    }
    
    for attempt in range(RETRY_TIMES):
        try:
            resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            data = resp.json()
            pages = data.get("query", {}).get("pages", [])
            if pages:
                content = pages[0].get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", "")
                return content
        except Exception as e:
            if attempt < RETRY_TIMES - 1:
                time.sleep(2)
            else:
                print(f"  ✗ 获取失败 {title}: {e}")
    return ""


def parse_operator_info(title, content):
    """解析干员信息（从 wikitext 提取）"""
    if not content:
        return None
    
    info = {"name": title, "raw": content[:5000]}  # 保留前5000字符
    
    # 提取职业
    profession_match = re.search(r'\|职业\s*=\s*(\S+)', content)
    if profession_match:
        info["profession"] = profession_match.group(1).strip()
    
    # 提取星级
    star_match = re.search(r'\|星级\s*=\s*(\d+)', content)
    if star_match:
        info["rarity"] = int(star_match.group(1))
    
    # 提取分支
    branch_match = re.search(r'\|分支\s*=\s*(\S+)', content)
    if branch_match:
        info["branch"] = branch_match.group(1).strip()
    
    # 提取阵营
    faction_match = re.search(r'\|阵营\s*=\s*(.+?)(?:\n\||\n$)', content)
    if faction_match:
        info["faction"] = faction_match.group(1).strip()
    
    # 提取特性
    feature_match = re.search(r'\|特性\s*=\s*(.+?)(?:\n\||\n$)', content, re.DOTALL)
    if feature_match:
        info["feature"] = feature_match.group(1).strip()[:200]
    
    # 提取标签
    tag_match = re.search(r'\|标签\s*=\s*(.+?)(?:\n\||\n$)', content)
    if tag_match:
        info["tags"] = tag_match.group(1).strip()
    
    # 提取简介/描述
    desc_match = re.search(r'\|简介\s*=\s*(.+?)(?:\n\||\n$)', content, re.DOTALL)
    if desc_match:
        info["description"] = desc_match.group(1).strip()[:300]
    
    # 提取技能（技能1/技能2/技能3）
    skills = []
    for i in range(1, 4):
        skill_name_match = re.search(rf'\|技能{i}名\s*=\s*(.+?)(?:\n\||\n$)', content)
        if skill_name_match:
            skill_name = skill_name_match.group(1).strip()
            skill_desc_match = re.search(rf'\|技能{i}描述\s*=\s*(.+?)(?:\n\||\n$)', content, re.DOTALL)
            skill_desc = skill_desc_match.group(1).strip()[:200] if skill_desc_match else ""
            if skill_name:
                skills.append({"name": skill_name, "description": skill_desc})
    if skills:
        info["skills"] = skills
    
    return info


def crawl_operator(title):
    """爬取单个干员"""
    global stats
    content = get_page_content(title)
    info = parse_operator_info(title, content)
    
    if info:
        # 保存原始数据
        safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', title)
        filepath = os.path.join(RAW_DIR, f"{safe_name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        with stats_lock:
            stats["success"] += 1
            if stats["success"] % 20 == 0:
                print(f"  进度: {stats['success']}/{stats['total']} 成功, {stats['fail']} 失败")
        return info
    else:
        with stats_lock:
            stats["fail"] += 1
        return None


def main():
    print("=" * 60)
    print("PRTS Wiki 明日方舟干员数据爬取")
    print("=" * 60)
    
    # 1. 获取干员列表
    operators = get_operator_list()
    stats["total"] = len(operators)
    
    # 保存干员列表
    with open(os.path.join(OUTPUT_DIR, "operator_list.json"), "w", encoding="utf-8") as f:
        json.dump(operators, f, ensure_ascii=False, indent=2)
    
    # 2. 多线程爬取
    print(f"\n开始多线程爬取（{MAX_WORKERS} 线程并发）...")
    start_time = time.time()
    
    all_info = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(crawl_operator, op): op for op in operators}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_info.append(result)
    
    elapsed = time.time() - start_time
    
    # 3. 保存汇总数据
    print(f"\n爬取完成！耗时 {elapsed:.1f} 秒")
    print(f"成功: {stats['success']}, 失败: {stats['fail']}")
    
    with open(os.path.join(OUTPUT_DIR, "all_operators.json"), "w", encoding="utf-8") as f:
        json.dump(all_info, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {OUTPUT_DIR}")
    print(f"  - operator_list.json (干员列表)")
    print(f"  - all_operators.json (所有干员信息)")
    print(f"  - raw/ (每个干员的单独文件)")


if __name__ == "__main__":
    main()
