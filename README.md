# AI翻译校对程序

## 📁 项目结构

```
ai_proofreader/
├── input_en/              # 英文输入文件夹
├── input_zh-sc/           # 中文输入文件夹
├── output/
│   └── en_modified/       # 修改输出文件夹
├── report/                # 报告文件夹
├── main.py               # 主程序
├── proofreader.py        # 校对模块
├── api_client.py         # API客户端
├── config.py             # 配置文件
├── utils.py              # 工具函数
└── README.md             # 使用说明
```

## 🚀 使用方法

### 1. 准备文件
将中英文文件分别放入对应的输入文件夹：
- 中文原文 → `input_zh-sc/`
- 英文翻译 → `input_en/`

### 2. 运行程序
```bash
python main.py
```

### 3. 选择要处理的文件
程序会显示所有可匹配的文件对，你可以：
- 输入文件编号（如：1 3 5）选择特定文件
- 输入 `all` 处理所有文件

### 4. 选择处理模式
当选择多个文件时，程序会询问处理方式：
- **串行处理**：按顺序逐个处理文件（稳定可靠）
- **并行处理**：同时处理多个文件（速度快，资源消耗大）

### 5. 查看结果
- **修改后的英文文件**：`output/en_modified/`
- **单个文件报告**：`report/filename_report.json`
- **总报告**：`report/summary_report.json`

## 📊 功能特点

### 🔍 智能文件匹配
- 自动扫描文件夹内的所有JSON文件
- 根据文件名匹配中英文文件对
- 支持多种命名格式：
  - 基础匹配：`filename.json` ↔ `filename.json`
  - 后缀匹配：`filename_en.json` ↔ `filename_zh-sc.json`

### 🎯 交互式选择
- 清晰显示所有可处理的文件对
- 支持选择单个或多个文件
- 可选择处理所有文件

### 🛡️ 安全处理
- **不修改原始输入文件**
- 在独立的输出文件夹中创建修改副本
- 保留原始数据完整性

### ⚡ 多层并发处理
程序支持三个层级的并发处理：

**1. 请求级并发**：
- 同时发送多个AI请求
- 提高API利用率
- 减少总体处理时间

**2. 文件级并发**：
- 同时处理多个文件
- 用户可选择串行或并行模式
- 适合批量处理场景

**3. 数据级并发**：
- 单文件内逐条独立处理
- 更好的错误隔离
- 精细化的进度控制

### 📈 智能修改策略
根据评分自动调整修改程度：
- **分数 < 50**：大幅修改句式和结构
- **50-75**：适度润色，改善表达
- **75-85**：少量修正明显错误
- **≥ 85**：不修改或仅微调个别词汇

## ⚙️ 配置说明

### 多环境配置
程序支持两种配置模式：

**生产环境配置** (`config.py`)：
- 包含完整的配置和安全的占位符
- 适合发布和分享
- API密钥需要用户自行填写

**开发环境配置** (`config_dev.py`)：
- 包含真实的API密钥和本地配置
- 适合本地开发和测试
- 已在 `.gitignore` 中排除，确保安全

首次使用前，请根据需要选择合适的配置文件：

```bash
# 生产环境（推荐）
copy config_template.py config.py

# 开发环境（本地使用）
copy config_dev.py config.py
```

### 核心配置参数
```python
class Config:
    # API配置
    API_KEY = "your-api-key-here"     # 你的API密钥
    BASE_URL = "https://yunwu.ai/v1"  # API基础URL
    MODEL_NAME = "gpt-5.2"            # 使用的模型名称
    
    # 处理配置
    BATCH_SIZE = 3                    # 批处理大小
    MAX_RETRIES = 3                   # 最大重试次数
    TEMPERATURE = 0.0                 # AI温度参数
    
    # 并发配置
    CONCURRENT_REQUESTS = 5           # 同时处理的请求数量
    CONCURRENT_FILES = 3              # 同时处理的文件数量
    REQUEST_TIMEOUT = 30              # 请求超时时间(秒)
    FILE_PROCESSING_TIMEOUT = 300     # 文件处理超时时间(秒)
    POLLING_INTERVAL = 0.5            # 轮询间隔(秒)
```

## 📈 输出示例

### 交互界面
```
🔄 正在扫描输入文件夹...

📋 可用的文件对:
1. dialogue1
   中文: dialogue1.json
   英文: dialogue1.json
2. conversation1
   中文: conversation1.json
   英文: conversation1.json
3. project
   中文: project.json
   英文: project.json

💡 输入选项编号(用空格分隔)，或输入'all'处理所有文件:
请选择: 1 3
```

### 处理结果
```
✅ 校对完成
📊 总条数: 4
✅ 正确条数: 2
❌ 错误条数: 2
📈 准确率: 50.0%
⭐ 平均分: 0.0
✏️  总共修改条目: 3条

📂 输出位置:
  修改后的文件: output/en_modified
  单独报告文件: report
  总报告文件: report/summary_report.json
📁 输入文件夹: input_en, input_zh-sc (未修改)
```

## 🔧 注意事项

1. **文件配对**：确保中英文文件的条目数量和顺序一致
2. **JSON格式**：文件必须是有效的JSON格式
3. **字段要求**：每条记录需要包含 `name` 和文本字段（message/text/content等）
4. **备份建议**：虽然程序不修改原文件，但仍建议备份重要数据
5. **API密钥**：请在 `config.py` 中配置有效的API密钥
6. **并发处理**：并行模式会同时消耗更多API资源，请根据API限制合理选择
7. **超时设置**：长时间处理的文件可能会触发超时，可根据需要调整配置参数

## 📝 报告格式

### 单个文件报告 (`filename_report.json`)
```json
{
  "file_info": {
    "filename": "dialogue1.json",
    "base_name": "dialogue1",
    "total_items": 5,
    "modified_items": 2
  },
  "reports": [
    {
      "original_index": 0,
      "name": "张三",
      "source_text": "你好",
      "target_text": "Hello",
      "score": 85,
      "modified_text": "Hello",
      "comment": "翻译准确",
      "is_correct": true
    }
  ]
}
```

### 总报告 (`summary_report.json`)
包含所有处理文件的统计信息和详细报告。

## 🆘 常见问题

**Q: 如何添加新的文件？**
A: 直接将新文件放入相应的输入文件夹，确保文件名匹配即可。

**Q: 如何处理大量文件？**
A: 建议分批处理，使用交互式选择功能选择需要处理的文件。

**Q: 修改后的文件在哪里？**
A: 在 `output/en_modified/` 文件夹中，原文件保持不变。

**Q: 如何查看具体的修改内容？**
A: 查看 `report/` 文件夹中的相应报告文件。

**Q: 什么时候应该使用并行处理？**
A: 处理大量文件且API有足够并发限制时使用。对于少量文件或不稳定网络，建议使用串行处理。

**Q: 为什么有些配置在config_dev.py中？**
A: config_dev.py包含开发环境的真实API配置，为了安全考虑已被.gitignore排除，不会提交到代码仓库。