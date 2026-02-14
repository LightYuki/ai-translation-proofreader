from api_client import AIClient
from config import Config
import json
import re

class Proofreader:
    def __init__(self):
        self.ai = AIClient()

    def _build_prompt(self, source_text, target_text, mode="check"):
        """构建校对提示词（优化版，减少token消耗）"""
        if mode == "check":
            prompt = f"""你是翻译校对员，请评估以下翻译质量并返回JSON：

中文: {source_text}
英文: {target_text}

返回格式：
{{
    "score": 0-100分数,
    "is_correct": true/false,
    "comment": "简要评价"
}}

要求：必须返回有效的JSON"""
        elif mode == "modify":
            prompt = f"""你是翻译编辑，请根据评分修改英文翻译：

中文: {source_text}
英文: {target_text}

修改策略：
分数<50：大幅修改
50-75：适度润色
75-85：少量修正
≥85：不修改

返回格式：
{{
    "modified_text": "修改后的英文翻译"
}}

要求：必须返回有效的JSON，modified_text是完整的新翻译"""
        
        return prompt

    def _parse_ai_response(self, response_text):
        """解析AI响应，提取JSON内容"""
        # 如果响应是列表，提取其中的文本内容
        if isinstance(response_text, list):
            if len(response_text) > 0 and isinstance(response_text[0], dict):
                response_text = response_text[0].get('text', str(response_text))
            else:
                response_text = str(response_text)
            
        try:
            # 首先尝试直接解析
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            # 查找第一个 { 和最后一个 } 之间的内容
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    json_str = match.group(0)
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
                
            # 如果还是失败，返回错误信息
            return {
                "is_correct": False,
                "issues": [],
                "overall_score": 0,
                "comment": "AI响应格式错误",
                "raw_response": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }

    def _smart_modify(self, source_text, target_text, score):
        """根据分数智能修改翻译文本（简化版）"""
        try:
            # 85分以上不修改
            if score >= 85:
                return {"modified_text": target_text}
            
            # 构建修改提示词
            prompt = self._build_prompt(source_text, target_text, mode="modify")
            
            # 调用AI进行修改
            result = self.ai.chat([{"role": "user", "content": prompt}])
            
            # 解析修改结果
            if isinstance(result, list):
                if len(result) > 0 and isinstance(result[0], dict):
                    result = result[0].get('text', str(result))
                else:
                    result = str(result)
            
            try:
                modification_result = json.loads(result.strip())
                return modification_result
            except json.JSONDecodeError:
                # 如果解析失败，返回原始文本
                return {"modified_text": target_text}
                
        except Exception as e:
            # 如果修改过程出错，返回原始文本
            return {"modified_text": target_text}
    
    def proofread_batch(self, batch):
        """
        batch: [{"index":0,"name":...,"source":...,"target":...}, ...]
        返回 JSON 校对结果，包含智能修改功能
        """
        reports = []

        for item in batch:
            # 第一步：校对评分
            check_prompt = self._build_prompt(item['source'], item['target'], mode="check")

            try:
                # 调用AI接口进行校对
                check_result = self.ai.chat([{"role": "user", "content": check_prompt}])

                # 解析校对结果
                parsed_result = self._parse_ai_response(check_result)
                
                # 获取评分
                score = parsed_result.get('overall_score', 0)
                issues = parsed_result.get('issues', [])
                
                # 根据分数决定是否进行修改
                modification_result = self._smart_modify(
                    item['source'], 
                    item['target'], 
                    score
                )

                # 构建精简报告
                final_report = {
                    "original_index": item['index'],
                    "name": item['name'],
                    "source_text": item['source'],
                    "target_text": item['target'],
                    "score": score,
                    "modified_text": modification_result.get('modified_text', item['target']),
                    "comment": parsed_result.get('comment', ''),
                    "is_correct": parsed_result.get('is_correct', False)
                }

                reports.append(final_report)

            except Exception as e:
                # 处理各种异常
                reports.append({
                    "original_index": item['index'],
                    "name": item['name'],
                    "source_text": item['source'],
                    "target_text": item['target'],
                    "score": 0,
                    "issues": [],
                    "modified_text": item['target'],
                    "changes_made": [],
                    "modification_level": f"处理失败: {str(e)}",
                    "comment": f"处理出错: {str(e)}",
                    "is_correct": False,
                    "error": str(e)
                })

        return reports
