#!/usr/bin/env python3
# 测试脚本 - 演示所有功能

import os
import sys

def test_full_workflow():
    print("🧪 AI翻译校对程序功能测试")
    print("=" * 50)
    
    # 检查文件结构
    print("\n📁 检查文件夹结构:")
    folders = ['input_en', 'input_zh-sc', 'output/en_modified', 'report']
    for folder in folders:
        exists = os.path.exists(folder)
        status = "✅ 存在" if exists else "❌ 不存在"
        print(f"  {folder}: {status}")
    
    # 检查输入文件
    print("\n📚 检查输入文件:")
    en_files = os.listdir('input_en') if os.path.exists('input_en') else []
    zh_files = os.listdir('input_zh-sc') if os.path.exists('input_zh-sc') else []
    print(f"  英文文件 ({len(en_files)}个): {en_files}")
    print(f"  中文文件 ({len(zh_files)}个): {zh_files}")
    
    # 检查输出文件
    print("\n💾 检查输出文件:")
    if os.path.exists('output/en_modified'):
        modified_files = os.listdir('output/en_modified')
        print(f"  修改后的文件 ({len(modified_files)}个): {modified_files}")
    
    if os.path.exists('report'):
        report_files = os.listdir('report')
        print(f"  报告文件 ({len(report_files)}个): {report_files}")
    
    print("\n🚀 程序特点:")
    print("  ✅ 交互式文件选择")
    print("  ✅ 不修改原始输入文件")
    print("  ✅ 在output/en_modified中创建修改副本")
    print("  ✅ 按文件名生成单独报告")
    print("  ✅ 支持批量处理")
    print("  ✅ 智能修改策略")
    
    print("\n💡 使用方法:")
    print("  1. 将文件放入 input_en/ 和 input_zh-sc/ 文件夹")
    print("  2. 运行: python main.py")
    print("  3. 根据提示选择要处理的文件")
    print("  4. 查看 output/en_modified/ 中的修改结果")
    print("  5. 查看 report/ 中的详细报告")

if __name__ == "__main__":
    test_full_workflow()