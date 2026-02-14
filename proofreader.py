from api_client import AIClient
from config import Config
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class Proofreader:
    def __init__(self):
        self.ai = AIClient()

    def _build_prompt(self, source_text, target_text, mode="check"):
        """构建校对提示词（从配置读取模板）"""
        if mode == "check":
            return Config.CHECK_PROMPT_TEMPLATE.format(
                source_text=source_text,
                target_text=target_text
            )
        elif mode == "modify":
            return Config.MODIFY_PROMPT_TEMPLATE.format(
                source_text=source_text,
                target_text=target_text
            )
        else:
            raise ValueError(f"不支持的模式: {mode}")

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
    
    def _process_single_item(self, item):
        """处理单个校对项目（用于并发执行）"""
        try:
            # 第一步：校对评分
            check_prompt = self._build_prompt(item['source'], item['target'], mode="check")
            
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
            
            return final_report
            
        except Exception as e:
            # 处理各种异常
            return {
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
            }
    
    def _poll_process_batch(self, batch):
        """轮询并发处理批次"""
        reports = []
        
        # 使用线程池进行并发处理
        with ThreadPoolExecutor(max_workers=Config.CONCURRENT_REQUESTS) as executor:
            # 提交所有任务
            future_to_item = {
                executor.submit(self._process_single_item, item): item 
                for item in batch
            }
            
            # 轮询获取结果
            completed_futures = set()
            while len(completed_futures) < len(future_to_item):
                for future in future_to_item:
                    if future not in completed_futures and future.done():
                        try:
                            result = future.result(timeout=Config.REQUEST_TIMEOUT)
                            reports.append(result)
                            completed_futures.add(future)
                        except Exception as e:
                            item = future_to_item[future]
                            error_report = {
                                "original_index": item['index'],
                                "name": item['name'],
                                "source_text": item['source'],
                                "target_text": item['target'],
                                "score": 0,
                                "issues": [{"type": "超时错误", "description": str(e)}],
                                "modified_text": item['target'],
                                "comment": f"处理超时: {str(e)}",
                                "is_correct": False,
                                "style_type": "超时处理",
                                "style_applied": "超时处理",
                                "changes_reason": str(e),
                                "modification_level": f"处理超时: {str(e)}",
                                "error": str(e)
                            }
                            reports.append(error_report)
                            completed_futures.add(future)
                
                # 如果还有未完成的任务，短暂休眠
                if len(completed_futures) < len(future_to_item):
                    time.sleep(Config.POLLING_INTERVAL)
        
        # 按原始索引排序确保顺序一致
        reports.sort(key=lambda x: x['original_index'])
        return reports
    
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
        使用轮询并发处理提高效率
        """
        # 使用轮询并发处理
        return self._poll_process_batch(batch)
