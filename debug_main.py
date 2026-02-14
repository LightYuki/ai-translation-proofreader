# 调试版本的主程序
import os
from tqdm import tqdm
from config import Config
from utils import load_json, save_json, validate_structure, chunk_list, detect_text_field
from proofreader import Proofreader
import json

def debug_run():
    print("🔄 正在加载数据...")
    try:
        src = load_json("data/source.json")
        tgt = load_json("data/translation.json")
        print(f"源数据: {src}")
        print(f"翻译数据: {tgt}")
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return

    print(f"📄 Source 条数: {len(src)}")
    print(f"📄 Target 条数: {len(tgt)}")

    try:
        validate_structure(src, tgt)
    except (ValueError, KeyError) as e:
        print(f"❌ 数据结构验证失败: {e}")
        return

    proofreader = Proofreader()

    print("🔄 正在合并数据...")
    merged = []
    for i, (s, t) in enumerate(zip(src, tgt)):
        print(f"\n处理第{i}条数据:")
        print(f"  源数据: {s}")
        print(f"  翻译数据: {t}")
        
        source_field = detect_text_field(s)
        target_field = detect_text_field(t)
        print(f"  检测到源字段: {source_field}")
        print(f"  检测到目标字段: {target_field}")
        
        if not source_field or not target_field:
            print(f"⚠ 第{i}条字段异常，跳过")
            continue
            
        # 安全地获取和处理文本内容
        try:
            source_value = s[source_field]
            target_value = t[target_field]
            print(f"  源值: {source_value} (类型: {type(source_value)})")
            print(f"  目标值: {target_value} (类型: {type(target_value)})")
            
            # 确保转换为字符串并去除空白
            source_text = str(source_value).strip() if source_value is not None else ""
            target_text = str(target_value).strip() if target_value is not None else ""
            print(f"  处理后源文本: '{source_text}'")
            print(f"  处理后目标文本: '{target_text}'")
            
            # 验证文本不为空
            if not source_text or not target_text:
                print(f"⚠ 第{i}条文本内容为空，跳过")
                continue
                
            merged.append({
                "index": i,
                "name": s.get("name"),
                "source": source_text,
                "target": target_text
            })
            print(f"  ✅ 成功添加到合并列表")
            
        except Exception as e:
            print(f"⚠ 第{i}条数据处理出错: {e}")
            continue

    if not merged:
        print("❌ 没有有效的数据可以处理")
        return

    print(f"✅ 合并完成，共 {len(merged)} 条待校对")
    print(f"合并后的数据: {merged}")

    all_reports = []
    print("🤖 开始AI校对...")
    
    for batch in list(chunk_list(merged, Config.BATCH_SIZE)):
        print(f"处理批次: {batch}")
        try:
            reports = proofreader.proofread_batch(batch)
            print(f"批次结果: {reports}")
            all_reports.extend(reports)
        except Exception as e:
            print(f"❌ 批次处理失败: {e}")
            import traceback
            traceback.print_exc()
            # 为失败的批次创建错误报告
            for item in batch:
                all_reports.append({
                    "original_index": item['index'],
                    "name": item['name'],
                    "source_text": item['source'],
                    "target_text": item['target'],
                    "is_correct": False,
                    "issues": [],
                    "overall_score": 0,
                    "comment": f"批次处理失败: {str(e)}",
                    "error": str(e)
                })

    print(f"所有报告: {all_reports}")
    
    # 生成汇总报告
    summary_report = {
        "summary": {
            "total_items": len(all_reports),
            "correct_items": sum(1 for r in all_reports if r.get('is_correct', False)),
            "incorrect_items": len(all_reports) - sum(1 for r in all_reports if r.get('is_correct', False)),
            "accuracy_rate": 0.0,
            "average_score": 0.0,
            "issue_statistics": {}
        },
        "detailed_reports": all_reports
    }
    
    os.makedirs("output", exist_ok=True)
    output_path = "output/debug_report.json"
    save_json(summary_report, output_path)

    print("====================================")
    print("✅ 调试完成")
    print(f"📂 输出文件: {output_path}")
    print("====================================")

if __name__ == "__main__":
    debug_run()