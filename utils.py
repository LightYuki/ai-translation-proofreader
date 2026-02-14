import json

POSSIBLE_TEXT_FIELDS = ["message", "text", "content", "dialogue"]

def detect_text_field(item: dict):
    """检测文本字段，确保返回可用的字段名"""
    for field in POSSIBLE_TEXT_FIELDS:
        if field in item:
            value = item[field]
            # 检查值是否为有效文本
            if value is not None:
                return field
    return None

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validate_structure(src: list, tgt: list):
    if len(src) != len(tgt):
        raise ValueError(f"❌ 条目数量不一致: {len(src)} != {len(tgt)}")
    for i, (s, t) in enumerate(zip(src, tgt)):
        source_field = detect_text_field(s)
        target_field = detect_text_field(t)
        if not source_field:
            raise KeyError(f"❌ source 第{i}条找不到文本字段 (message/text/content/dialogue)")
        if not target_field:
            raise KeyError(f"❌ target 第{i}条找不到文本字段 (message/text/content/dialogue)")
        source_name = s.get("name")
        target_name = t.get("name")
        if source_name and target_name and source_name != target_name:
            print(f"⚠ 第{i}条 name 不一致: {source_name} != {target_name}")

def validate_and_extract_text(data_item, field_name):
    """安全地提取和验证文本内容"""
    if field_name not in data_item:
        return None
        
    value = data_item[field_name]
    
    # 处理不同类型的值
    if isinstance(value, str):
        return value.strip()
    elif isinstance(value, (list, tuple)):
        # 如果是列表，取第一个元素或连接所有元素
        if len(value) > 0:
            if isinstance(value[0], str):
                return ' '.join(str(v).strip() for v in value if v is not None)
            else:
                return str(value[0]).strip()
        else:
            return ""
    elif value is None:
        return ""
    else:
        return str(value).strip()

def chunk_list(data: list, size: int):
    for i in range(0, len(data), size):
        yield data[i:i + size]
