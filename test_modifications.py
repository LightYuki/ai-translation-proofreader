# 测试不同分数区间的修改策略
import json
from proofreader import Proofreader

def test_different_scores():
    """测试不同质量翻译的修改效果"""
    
    test_cases = [
        {
            "name": "低质量翻译(35分)",
            "source": "这是一个测试文本",
            "target": "Thjs is an testing word."
        },
        {
            "name": "中等质量翻译(65分)",
            "source": "今天天气很好",
            "target": "Today weather is good"
        },
        {
            "name": "较高质量翻译(80分)",
            "source": "我们需要尽快完成这个项目",
            "target": "We need to finish this project as soon as possible"
        },
        {
            "name": "高质量翻译(95分)",
            "source": "人工智能正在改变我们的生活方式",
            "target": "Artificial intelligence is transforming our way of life"
        }
    ]
    
    proofreader = Proofreader()
    
    print("🔍 智能修改功能测试")
    print("=" * 50)
    
    for i, case in enumerate(test_cases):
        print(f"\n📋 测试案例 {i+1}: {case['name']}")
        print(f"📝 中文原文: {case['source']}")
        print(f"🔤 英文翻译: {case['target']}")
        
        # 创建测试批次
        batch = [{
            "index": i,
            "name": "测试",
            "source": case['source'],
            "target": case['target']
        }]
        
        try:
            # 执行校对和修改
            reports = proofreader.proofread_batch(batch)
            report = reports[0]
            
            print(f"⭐ 评分: {report['score']}")
            print(f"🔧 修改级别: {report['modification_level']}")
            print(f"💬 评语: {report['comment']}")
            
            if report['target_text'] != report['modified_text']:
                print(f"🔄 修改后: {report['modified_text']}")
                print("📝 具体修改:")
                for change in report['changes_made']:
                    print(f"  • {change['original']} → {change['modified']}")
                    print(f"    原因: {change['reason']}")
            else:
                print("✅ 无需修改")
                
        except Exception as e:
            print(f"❌ 处理出错: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_different_scores()