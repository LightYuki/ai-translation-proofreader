import os
import glob
from tqdm import tqdm
from config import Config
from utils import load_json, save_json, validate_structure, chunk_list, detect_text_field
from proofreader import Proofreader
import json

def generate_summary_report(reports):
    """生成汇总报告"""
    total_items = len(reports)
    correct_items = sum(1 for r in reports if r.get('is_correct', False))
    incorrect_items = total_items - correct_items

    avg_score = sum(r.get('score', 0) for r in reports) / total_items if total_items > 0 else 0
    
    # 统计修改级别
    modification_levels = {}
    for report in reports:
        level = report.get('modification_level', '未知')
        modification_levels[level] = modification_levels.get(level, 0) + 1

    # 统计问题类型
    issue_types = {}
    for report in reports:
        for issue in report.get('issues', []):
            issue_type = issue.get('type', '未知')
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

    summary = {
        "summary": {
            "total_items": total_items,
            "correct_items": correct_items,
            "incorrect_items": incorrect_items,
            "accuracy_rate": round(correct_items / total_items * 100, 2) if total_items > 0 else 0,
            "average_score": round(avg_score, 2),
            "issue_statistics": issue_types,
            "modification_statistics": modification_levels
        },
        "detailed_reports": reports
    }

    return summary

def find_matching_files(en_folder, zh_folder):
    """查找匹配的中英文文件对"""
    en_files = {}
    zh_files = {}
    
    # 收集英文文件
    for file_path in glob.glob(os.path.join(en_folder, "*.json")):
        filename = os.path.basename(file_path)
        # 移除可能的后缀
        base_name = filename.replace('_en.json', '').replace('.json', '')
        en_files[base_name] = file_path
    
    # 收集中文文件
    for file_path in glob.glob(os.path.join(zh_folder, "*.json")):
        filename = os.path.basename(file_path)
        # 移除可能的后缀
        base_name = filename.replace('_zh-sc.json', '').replace('.json', '')
        zh_files[base_name] = file_path
    
    # 找到匹配的文件对
    file_pairs = []
    for base_name in en_files:
        if base_name in zh_files:
            file_pairs.append({
                'base_name': base_name,
                'en_file': en_files[base_name],
                'zh_file': zh_files[base_name]
            })
    
    return file_pairs

def select_files_interactive(file_pairs):
    """交互式选择要处理的文件"""
    if not file_pairs:
        print("❌ 没有找到匹配的文件对")
        return []
    
    print("\n📋 可用的文件对:")
    for i, pair in enumerate(file_pairs, 1):
        print(f"{i}. {pair['base_name']}")
        print(f"   中文: {os.path.basename(pair['zh_file'])}")
        print(f"   英文: {os.path.basename(pair['en_file'])}")
    
    print(f"\n💡 输入选项编号(用空格分隔)，或输入'all'处理所有文件:")
    user_input = input("请选择: ").strip()
    
    if user_input.lower() == 'all':
        return file_pairs
    
    try:
        selected_indices = [int(x.strip()) - 1 for x in user_input.split() if x.strip()]
        selected_pairs = [file_pairs[i] for i in selected_indices if 0 <= i < len(file_pairs)]
        return selected_pairs
    except ValueError:
        print("❌ 输入格式错误，请输入数字或'all'")
        return []

def process_file_pair(en_file, zh_file, proofreader):
    """处理单个文件对"""
    print(f"\n🔄 正在处理文件对: {os.path.basename(en_file)} <-> {os.path.basename(zh_file)}")
    
    try:
        src = load_json(zh_file)
        tgt = load_json(en_file)
        # 保存原始翻译数据用于后续修改
        original_tgt = load_json(en_file)
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return None

    print(f"📄 中文条数: {len(src)}")
    print(f"📄 英文条数: {len(tgt)}")

    try:
        validate_structure(src, tgt)
    except (ValueError, KeyError) as e:
        print(f"❌ 数据结构验证失败: {e}")
        return None

    print("🔄 正在合并数据...")
    merged = []
    for i, (s, t) in enumerate(zip(src, tgt)):
        source_field = detect_text_field(s)
        target_field = detect_text_field(t)
        
        if not source_field or not target_field:
            print(f"⚠ 第{i}条字段异常，跳过")
            continue
            
        # 安全地获取和处理文本内容
        try:
            source_value = s[source_field]
            target_value = t[target_field]
            
            # 确保转换为字符串并去除空白
            source_text = str(source_value).strip() if source_value is not None else ""
            target_text = str(target_value).strip() if target_value is not None else ""
            
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
            
        except Exception as e:
            print(f"⚠ 第{i}条数据处理出错: {e}")
            continue

    if not merged:
        print("❌ 没有有效的数据可以处理")
        return None

    print(f"✅ 合并完成，共 {len(merged)} 条待校对")

    all_reports = []
    print("🤖 开始AI校对...")
    
    batch_count = 0
    for batch in tqdm(list(chunk_list(merged, Config.BATCH_SIZE)), desc="处理批次"):
        batch_count += 1
        try:
            reports = proofreader.proofread_batch(batch)
            all_reports.extend(reports)
        except Exception as e:
            print(f"❌ 批次 {batch_count} 处理失败: {e}")
            # 为失败的批次创建错误报告
            for item in batch:
                all_reports.append({
                    "original_index": item['index'],
                    "name": item['name'],
                    "source_text": item['source'],
                    "target_text": item['target'],
                    "score": 0,
                    "modified_text": item['target'],
                    "comment": f"批次处理失败: {str(e)}",
                    "is_correct": False,
                    "error": str(e)
                })
    
    return {
        'src_data': src,
        'tgt_data': tgt,
        'original_tgt': original_tgt,
        'reports': all_reports,
        'filename': os.path.basename(en_file)
    }

def run():
    print("🔄 正在扫描输入文件夹...")
    
    EN_FOLDER = "input_en"
    ZH_FOLDER = "input_zh-sc"
    MODIFIED_FOLDER = "output/en_modified"
    REPORT_FOLDER = "report"
    
    # 检查文件夹是否存在
    if not os.path.exists(EN_FOLDER):
        print(f"❌ 英文输入文件夹不存在: {EN_FOLDER}")
        return
    if not os.path.exists(ZH_FOLDER):
        print(f"❌ 中文输入文件夹不存在: {ZH_FOLDER}")
        return
    
    # 创建输出文件夹
    os.makedirs(MODIFIED_FOLDER, exist_ok=True)
    os.makedirs(REPORT_FOLDER, exist_ok=True)
    
    # 查找匹配的文件对
    file_pairs = find_matching_files(EN_FOLDER, ZH_FOLDER)
    
    if not file_pairs:
        print("❌ 没有找到匹配的文件对")
        return
    
    # 用户选择要处理的文件
    selected_pairs = select_files_interactive(file_pairs)
    
    if not selected_pairs:
        print("❌ 没有选择要处理的文件")
        return
    
    print(f"\n✅ 已选择 {len(selected_pairs)} 个文件对进行处理")
    
    proofreader = Proofreader()
    all_results = []
    
    # 处理每个选中的文件对
    for pair in selected_pairs:
        result = process_file_pair(pair['en_file'], pair['zh_file'], proofreader)
        if result:
            # 添加文件名信息用于报告命名
            result['base_name'] = pair['base_name']
            all_results.append(result)
    
    if not all_results:
        print("❌ 没有成功处理任何文件")
        return

    # 处理所有结果并生成报告
    total_modified = 0
    all_detailed_reports = []
    
    # 为每个文件生成单独的报告并在output中创建修改后的副本
    for result in all_results:
        reports = result['reports']
        original_tgt = result['original_tgt']
        filename = result['filename']
        base_name = result['base_name']
        
        # 创建修改后的英文文件副本
        modified_count = 0
        for report in reports:
            original_index = report['original_index']
            if report['target_text'] != report['modified_text']:
                # 更新翻译文件中的对应条目
                target_field = detect_text_field(original_tgt[original_index])
                if target_field:
                    original_tgt[original_index][target_field] = report['modified_text']
                    modified_count += 1
        
        # 保存修改后的翻译文件到output/en_modified/
        modified_filename = filename
        save_json(original_tgt, os.path.join(MODIFIED_FOLDER, modified_filename))
        total_modified += modified_count
        
        # 为该文件生成单独的报告
        file_report = {
            "file_info": {
                "filename": filename,
                "base_name": base_name,
                "total_items": len(reports),
                "modified_items": modified_count
            },
            "reports": reports
        }
        
        # 保存单独的报告文件
        report_filename = f"{base_name}_report.json"
        save_json(file_report, os.path.join(REPORT_FOLDER, report_filename))
        
        # 添加到总报告
        all_detailed_reports.extend(reports)
        
        print(f"📁 {filename}: 修改了 {modified_count} 条")
    
    # 生成总汇总报告
    summary_report = generate_summary_report(all_detailed_reports)
    
    # 保存总报告
    total_report_path = os.path.join(REPORT_FOLDER, "summary_report.json")
    save_json(summary_report, total_report_path)

    print("====================================")
    print("✅ 校对完成")
    print(f"📊 总条数: {summary_report['summary']['total_items']}")
    print(f"✅ 正确条数: {summary_report['summary']['correct_items']}")
    print(f"❌ 错误条数: {summary_report['summary']['incorrect_items']}")
    print(f"📈 准确率: {summary_report['summary']['accuracy_rate']}%")
    print(f"⭐ 平均分: {summary_report['summary']['average_score']}")
    print(f"✏️  总共修改条目: {total_modified}条")
    
    print(f"\n📂 输出位置:")
    print(f"  修改后的文件: {MODIFIED_FOLDER}")
    print(f"  单独报告文件: {REPORT_FOLDER}")
    print(f"  总报告文件: {total_report_path}")
    print(f"📁 输入文件夹: {EN_FOLDER}, {ZH_FOLDER} (未修改)")
    print("====================================")

if __name__ == "__main__":
    run()
