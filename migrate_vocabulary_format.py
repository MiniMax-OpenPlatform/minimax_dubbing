#!/usr/bin/env python3
"""
数据库迁移脚本：将专有词汇表从字符串数组格式转换为字典格式
从: ['爸爸|HAHA']
到: [{'序号': 1, '词汇': '爸爸', '译文': 'HAHA'}]
"""
import os
import sys

# 添加项目路径
sys.path.append('/home/Devin/minimax_translation')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from projects.models import Project

def migrate_vocabulary_format():
    """迁移专有词汇表格式"""

    print("🔄 开始迁移专有词汇表格式...")

    # 获取所有项目
    projects = Project.objects.all()
    total_projects = projects.count()
    updated_count = 0

    print(f"📊 找到 {total_projects} 个项目需要检查")

    for project in projects:
        print(f"\n📝 检查项目: {project.name} (ID: {project.id})")

        if not project.custom_vocabulary:
            print("  ⚪ 专有词汇表为空，跳过")
            continue

        # 检查当前格式
        print(f"  📋 当前格式: {project.custom_vocabulary} (类型: {type(project.custom_vocabulary)})")

        # 如果已经是字典格式，跳过
        if (isinstance(project.custom_vocabulary, list) and
            len(project.custom_vocabulary) > 0 and
            isinstance(project.custom_vocabulary[0], dict) and
            '词汇' in project.custom_vocabulary[0]):
            print("  ✅ 已经是字典格式，跳过")
            continue

        # 需要转换的情况
        new_vocabulary = []

        if isinstance(project.custom_vocabulary, list):
            # 处理字符串数组格式 ['爸爸|HAHA']
            for index, item in enumerate(project.custom_vocabulary):
                if isinstance(item, str) and '|' in item:
                    parts = item.strip().split('|')
                    if len(parts) >= 2:
                        new_vocabulary.append({
                            '序号': index + 1,
                            '词汇': parts[0].strip(),
                            '译文': parts[1].strip()
                        })
                        print(f"    🔄 转换: '{item}' → {new_vocabulary[-1]}")
                    else:
                        print(f"    ⚠️ 跳过格式错误的项: '{item}'")
                else:
                    print(f"    ⚠️ 跳过非字符串项: {item} (类型: {type(item)})")

        elif isinstance(project.custom_vocabulary, str):
            # 处理字符串格式
            lines = project.custom_vocabulary.split('\n')
            for index, line in enumerate(lines):
                if '|' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        new_vocabulary.append({
                            '序号': index + 1,
                            '词汇': parts[0].strip(),
                            '译文': parts[1].strip()
                        })
                        print(f"    🔄 转换: '{line}' → {new_vocabulary[-1]}")

        # 更新数据库
        if new_vocabulary:
            old_vocabulary = project.custom_vocabulary
            project.custom_vocabulary = new_vocabulary
            project.save()
            updated_count += 1

            print(f"  ✅ 更新成功!")
            print(f"  📤 旧格式: {old_vocabulary}")
            print(f"  📥 新格式: {new_vocabulary}")
        else:
            print("  ⚠️ 没有有效的词汇项可转换")

    print(f"\n🎉 迁移完成!")
    print(f"📊 总项目数: {total_projects}")
    print(f"✅ 成功更新: {updated_count}")
    print(f"⚪ 跳过: {total_projects - updated_count}")

def verify_migration():
    """验证迁移结果"""

    print("\n🔍 验证迁移结果...")

    projects = Project.objects.exclude(custom_vocabulary__exact=[])

    for project in projects:
        print(f"\n📝 项目: {project.name}")
        print(f"  📋 专有词汇表: {project.custom_vocabulary}")
        print(f"  📊 类型: {type(project.custom_vocabulary)}")

        if isinstance(project.custom_vocabulary, list) and len(project.custom_vocabulary) > 0:
            first_item = project.custom_vocabulary[0]
            print(f"  🔍 第一项类型: {type(first_item)}")
            if isinstance(first_item, dict):
                print(f"  ✅ 字典格式正确，包含键: {list(first_item.keys())}")
            else:
                print(f"  ❌ 格式错误，第一项不是字典")

if __name__ == "__main__":
    print("=" * 60)
    print("专有词汇表格式迁移脚本")
    print("=" * 60)

    # 执行迁移
    migrate_vocabulary_format()

    # 验证结果
    verify_migration()

    print("\n" + "=" * 60)
    print("迁移脚本执行完成!")
    print("=" * 60)