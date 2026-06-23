"""
明日方舟助手评估脚本
用法：python evaluate.py --model_path ./output --test_dir ./eval_data
"""
import json
import os
import argparse
import re
from difflib import SequenceMatcher
from collections import defaultdict


def load_test_set(filepath):
    """加载测试集"""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def keyword_match(prediction, keywords):
    """关键词匹配：预测答案是否包含关键词"""
    if not prediction or not keywords:
        return False
    # 至少匹配一半的关键词算正确
    matched = sum(1 for kw in keywords if kw in prediction)
    return matched >= max(1, len(keywords) // 2)


def text_similarity(text1, text2):
    """计算两段文本的相似度（0-1）"""
    if not text1 or not text2:
        return 0.0
    # 字符级相似度
    return SequenceMatcher(None, text1, text2).ratio()


def is_rejection(prediction, reject_keywords):
    """检测是否为拒绝回答"""
    if not prediction:
        return True
    return any(kw in prediction for kw in reject_keywords)


def evaluate_knowledge(predictions, test_set):
    """评估知识问答准确率"""
    results = []
    correct = 0
    by_type = defaultdict(lambda: {"correct": 0, "total": 0})
    
    for test in test_set:
        qid = test["id"]
        pred = predictions.get(qid, "")
        keywords = test["keywords"]
        is_correct = keyword_match(pred, keywords)
        
        if is_correct:
            correct += 1
            by_type[test["type"]]["correct"] += 1
        by_type[test["type"]]["total"] += 1
        
        results.append({
            "id": qid,
            "question": test["question"],
            "standard_answer": test["standard_answer"],
            "prediction": pred,
            "keywords": keywords,
            "correct": is_correct
        })
    
    accuracy = correct / len(test_set) if test_set else 0
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": len(test_set),
        "by_type": {k: {"accuracy": v["correct"]/v["total"], **v} for k, v in by_type.items()},
        "details": results
    }


def evaluate_roleplay(predictions, test_set):
    """评估角色扮演相似度"""
    results = []
    total_sim = 0
    by_operator = defaultdict(list)
    
    for test in test_set:
        qid = test["id"]
        pred = predictions.get(qid, "")
        reference = test["reference"]
        sim = text_similarity(pred, reference)
        total_sim += sim
        by_operator[test["operator"]].append(sim)
        
        results.append({
            "id": qid,
            "question": test["question"],
            "reference": reference,
            "prediction": pred,
            "similarity": sim
        })
    
    avg_sim = total_sim / len(test_set) if test_set else 0
    return {
        "avg_similarity": avg_sim,
        "total": len(test_set),
        "by_operator": {k: sum(v)/len(v) for k, v in by_operator.items()},
        "details": results
    }


def evaluate_hallucination(predictions, test_set):
    """评估幻觉率"""
    results = []
    rejected = 0
    
    for test in test_set:
        qid = test["id"]
        pred = predictions.get(qid, "")
        is_reject = is_rejection(pred, test["keywords_reject"])
        if is_reject:
            rejected += 1
        
        results.append({
            "id": qid,
            "question": test["question"],
            "prediction": pred,
            "rejected": is_reject,
            "fake_name": test["fake_name"]
        })
    
    reject_rate = rejected / len(test_set) if test_set else 0
    hallucination_rate = 1 - reject_rate
    return {
        "reject_rate": reject_rate,
        "hallucination_rate": hallucination_rate,
        "rejected": rejected,
        "total": len(test_set),
        "details": results
    }


def calculate_total_score(knowledge_acc, roleplay_sim, hallucination_rate, fluency_score=85):
    """计算总分
    - 知识准确率: 40%
    - 角色相似度: 25%
    - 幻觉控制: 20%（100 - 幻觉率）
    - 流畅度: 15%（人工打分，默认85）
    """
    score = (
        knowledge_acc * 100 * 0.40 +
        roleplay_sim * 100 * 0.25 +
        (100 - hallucination_rate * 100) * 0.20 +
        fluency_score * 0.15
    )
    return score


def get_grade(score):
    """获取等级"""
    if score >= 90:
        return "优秀 (A)"
    elif score >= 80:
        return "良好 (B)"
    elif score >= 70:
        return "中等 (C)"
    elif score >= 60:
        return "及格 (D)"
    else:
        return "不及格 (F)"


def main():
    parser = argparse.ArgumentParser(description="明日方舟助手评估")
    parser.add_argument("--predictions", type=str, required=True,
                        help="模型预测结果JSON文件")
    parser.add_argument("--test_dir", type=str, default="./eval_data",
                        help="测试集目录")
    parser.add_argument("--fluency_score", type=int, default=85,
                        help="流畅度人工评分（0-100）")
    parser.add_argument("--output", type=str, default="eval_report.json",
                        help="评估报告输出文件")
    args = parser.parse_args()
    
    # 加载预测结果
    with open(args.predictions, encoding="utf-8") as f:
        predictions = json.load(f)
    
    print("=" * 60)
    print("明日方舟助手评估报告")
    print("=" * 60)
    
    # 1. 知识问答
    print("\n[1/3] 知识问答准确率...")
    knowledge_tests = load_test_set(os.path.join(args.test_dir, "test_knowledge.json"))
    knowledge_result = evaluate_knowledge(predictions, knowledge_tests)
    print(f"  准确率: {knowledge_result['accuracy']*100:.1f}% ({knowledge_result['correct']}/{knowledge_result['total']})")
    print(f"  分题型:")
    for t, r in knowledge_result["by_type"].items():
        print(f"    {t}: {r['accuracy']*100:.1f}% ({r['correct']}/{r['total']})")
    
    # 2. 角色扮演
    print("\n[2/3] 角色扮演相似度...")
    roleplay_tests = load_test_set(os.path.join(args.test_dir, "test_roleplay.json"))
    roleplay_result = evaluate_roleplay(predictions, roleplay_tests)
    print(f"  平均相似度: {roleplay_result['avg_similarity']*100:.1f}%")
    
    # 3. 幻觉检测
    print("\n[3/3] 幻觉检测...")
    hallucination_tests = load_test_set(os.path.join(args.test_dir, "test_hallucination.json"))
    hallucination_result = evaluate_hallucination(predictions, hallucination_tests)
    print(f"  拒绝率: {hallucination_result['reject_rate']*100:.1f}%")
    print(f"  幻觉率: {hallucination_result['hallucination_rate']*100:.1f}%")
    
    # 4. 总分
    total_score = calculate_total_score(
        knowledge_result["accuracy"],
        roleplay_result["avg_similarity"],
        hallucination_result["hallucination_rate"],
        args.fluency_score
    )
    grade = get_grade(total_score)
    
    print("\n" + "=" * 60)
    print("综合评分")
    print("=" * 60)
    print(f"  知识准确率 (40%):  {knowledge_result['accuracy']*100:.1f} → {knowledge_result['accuracy']*100*0.40:.1f}")
    print(f"  角色相似度 (25%):  {roleplay_result['avg_similarity']*100:.1f} → {roleplay_result['avg_similarity']*100*0.25:.1f}")
    print(f"  幻觉控制   (20%):  {100-hallucination_result['hallucination_rate']*100:.1f} → {(100-hallucination_result['hallucination_rate']*100)*0.20:.1f}")
    print(f"  流畅度     (15%):  {args.fluency_score} → {args.fluency_score*0.15:.1f}")
    print(f"  ─────────────────────────")
    print(f"  总分: {total_score:.1f} / 100")
    print(f"  等级: {grade}")
    print("=" * 60)
    
    # 保存报告
    report = {
        "total_score": total_score,
        "grade": grade,
        "knowledge": {k: v for k, v in knowledge_result.items() if k != "details"},
        "roleplay": {k: v for k, v in roleplay_result.items() if k != "details"},
        "hallucination": {k: v for k, v in hallucination_result.items() if k != "details"},
        "fluency_score": args.fluency_score
    }
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {args.output}")


if __name__ == "__main__":
    main()
