class Config:
    # 请在此处填写你的API密钥
    API_KEY = "your-api-key-here"
    
    # API基础URL
    BASE_URL = "https://yunwu.ai/v1"
    
    # 使用的模型名称
    MODEL_NAME = "gpt-5.2"
    
    # 批处理大小
    BATCH_SIZE = 3
    
    # 最大重试次数
    MAX_RETRIES = 3
    
    # 温度参数
    TEMPERATURE = 0.0
    
    # 并发配置
    CONCURRENT_REQUESTS = 5  # 同时处理的请求数量
    REQUEST_TIMEOUT = 30     # 请求超时时间(秒)
    POLLING_INTERVAL = 0.5   # 轮询间隔(秒)
    
    # 文件并行处理配置
    CONCURRENT_FILES = 3     # 同时处理的文件数量
    FILE_PROCESSING_TIMEOUT = 300  # 文件处理超时时间(秒)
    
    # Prompt模板配置
    CHECK_PROMPT_TEMPLATE = """你是专业的翻译校对员，请评估以下翻译质量并返回JSON：

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
    
    MODIFY_PROMPT_TEMPLATE = """你是资深翻译编辑，请根据以下要求修改英文翻译：

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