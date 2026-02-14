from api_client import AIClient
from config import Config
import json
import re

class Proofreader:
    def __init__(self):
        self.ai = AIClient()

    def _build_prompt(self, source_text, target_text, mode="check"):
        """构建校对提示词（支持多种翻译风格）"""
        if mode == "check":
            prompt = f"""你是专业的翻译校对员，请评估以下翻译质量并返回JSON：

原文: {source_text}
译文: {target_text}

请按以下格式返回JSON结果：
{{
    "score": 0-100的整数分数,
    "is_correct": true/false,
    "style_type": "网络梗|meme|游戏标准|普通翻译",
    "comment": "简要评价翻译质量和风格适配度"
}}

评估要点：
1. 准确性：是否准确传达原意
2. 风格适配：是否符合目标风格要求
3. 本地化：是否自然流畅
4. 控制符：忽略@换页、\n换行、&选项隔断等控制符号"""
        elif mode == "modify":
            prompt = f"""你是资深翻译编辑，请根据以下要求修改英文翻译：

原文: {source_text}
译文: {target_text}

翻译风格要求：
- 若原文存在网络梗：使用2000年前后英文网络用语meme风格
- 若原文为英语：保持原文风格不变
- 若为游戏系统文本（提示、界面、任务等）：使用规范游戏标准用语
- 保证原意准确并进行本地化润色
- 忽略控制符（@换页、\n换行、&选项隔断）

修改策略：
分数<50：大幅重构，全面调整风格和表达
50-75：适度润色，优化风格适配
75-85：少量修正，微调表达细节
≥85：保持原样或仅微小调整

请按以下格式返回JSON：
{{
    "modified_text": "修改后的英文翻译",
    "style_applied": "实际应用的风格类型",
    "changes_reason": "主要修改原因说明"
}}

要求：必须返回有效的JSON，modified_text必须是完整的新翻译"""
        
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
                "score": 0,
                "comment": "AI响应格式错误",
                "raw_response": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }

    def _get_modification_level(self, score):
        """根据分数确定修改级别"""
        if score >= 85:
            return "无需修改"
        elif score >= 75:
            return "少量修正"
        elif score >= 50:
            return "适度润色"
        else:
            return "大幅重构"
    
    def _smart_modify(self, source_text, target_text, score):
        """根据分数智能修改翻译文本（支持多风格）"""
        try:
            # 85分以上不修改
            if score >= 85:
                return {
                    "modified_text": target_text,
                    "style_applied": "保持原样",
                    "changes_reason": "评分较高，无需修改"
                }
            
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
                # 确保必要字段存在
                if "modified_text" not in modification_result:
                    modification_result["modified_text"] = target_text
                if "style_applied" not in modification_result:
                    modification_result["style_applied"] = "未知风格"
                if "changes_reason" not in modification_result:
                    modification_result["changes_reason"] = "自动修改"
                return modification_result
            except json.JSONDecodeError:
                # 如果解析失败，返回原始文本
                return {
                    "modified_text": target_text,
                    "style_applied": "解析失败",
                    "changes_reason": "AI响应格式错误"
                }
                
        except Exception as e:
            # 如果修改过程出错，返回原始文本
            return {
                "modified_text": target_text,
                "style_applied": f"修改出错: {type(e).__name__}",
                "changes_reason": str(e)
            }
    
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
                score = parsed_result.get('score', 0)
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
                    "is_correct": parsed_result.get('is_correct', False),
                    "style_type": parsed_result.get('style_type', '普通翻译'),
                    "style_applied": modification_result.get('style_applied', '未应用'),
                    "changes_reason": modification_result.get('changes_reason', '无修改'),
                    "issues": issues,
                    "modification_level": self._get_modification_level(score)
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
                    "issues": [{"type": "处理错误", "description": str(e)}],
                    "modified_text": item['target'],
                    "comment": f"处理出错: {str(e)}",
                    "is_correct": False,
                    "style_type": "错误处理",
                    "style_applied": "错误处理",
                    "changes_reason": str(e),
                    "modification_level": f"处理失败: {str(e)}",
                    "error": str(e)
                })

        return reports
