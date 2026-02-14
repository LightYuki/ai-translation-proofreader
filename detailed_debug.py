# 更详细的调试版本
from api_client import AIClient
from config import Config
import json
import re

class DebugProofreader:
    def __init__(self):
        self.ai = AIClient()
        
    def debug_proofread_batch(self, batch):
        """
        详细调试版本的proofread_batch
        """
        reports = []
        
        for item in batch:
            print(f"调试 - 处理项目: {item}")
            
            # 构建提示词
            prompt = f"""你是一个专业的翻译校对员。请仔细校对以下中英文翻译质量，并严格按照指定的JSON格式返回结果。

中文原文: {item['source']}
英文翻译: {item['target']}

请按以下格式返回JSON结果：
{{
    "is_correct": true/false,
    "issues": [],
    "overall_score": 0-100的整数分数,
    "comment": "总体评价"
}}"""
            
            print(f"调试 - 提示词长度: {len(prompt)}")
            
            try:
                # 调用AI接口
                print("调试 - 开始调用AI接口...")
                result = self.ai.chat([{"role": "user", "content": prompt}])
                print(f"调试 - AI响应类型: {type(result)}")
                print(f"调试 - AI响应内容: {result}")
                
                # 解析结果
                print("调试 - 开始解析AI响应...")
                try:
                    parsed_result = json.loads(result.strip())
                    print(f"调试 - 解析成功: {parsed_result}")
                except Exception as parse_error:
                    print(f"调试 - JSON解析失败: {parse_error}")
                    parsed_result = {
                        "is_correct": False,
                        "issues": [],
                        "overall_score": 0,
                        "comment": f"JSON解析失败: {str(parse_error)}"
                    }
                
                # 添加元信息
                print("调试 - 构建最终报告...")
                final_report = {
                    "original_index": item['index'],
                    "name": item['name'],
                    "source_text": item['source'],
                    "target_text": item['target'],
                    **parsed_result
                }
                
                reports.append(final_report)
                print(f"调试 - 报告添加成功")
                
            except Exception as e:
                print(f"调试 - 处理异常: {e}")
                import traceback
                traceback.print_exc()
                
                # 处理各种异常
                reports.append({
                    "original_index": item['index'],
                    "name": item['name'],
                    "source_text": item['source'],
                    "target_text": item['target'],
                    "is_correct": False,
                    "issues": [],
                    "overall_score": 0,
                    "comment": f"处理出错: {str(e)}",
                    "error": str(e)
                })
        
        return reports

# 测试函数
def test_debug():
    from utils import load_json
    import os
    
    # 加载测试数据
    src = load_json("data/source.json")
    tgt = load_json("data/translation.json")
    
    # 合并数据
    merged = []
    for i, (s, t) in enumerate(zip(src, tgt)):
        merged.append({
            "index": i,
            "name": s.get("name"),
            "source": str(s["message"]).strip(),
            "target": str(t["message"]).strip()
        })
    
    print(f"测试数据: {merged}")
    
    # 创建调试校对器
    proofreader = DebugProofreader()
    
    # 执行校对
    reports = proofreader.debug_proofread_batch(merged)
    
    print(f"最终报告: {reports}")
    
    # 保存结果
    os.makedirs("output", exist_ok=True)
    with open("output/debug_detailed_report.json", "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    test_debug()