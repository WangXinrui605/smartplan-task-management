import os
import sys

# 1. 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. 配置Django设置（smart_plan和项目名一致）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_plan.settings")

import django
django.setup()

# 3. 导入模型（用实际应用名task）
from django.contrib.auth.models import User
from task.models import Category, Priority, Task
from datetime import date, timedelta

def populate():
    # ========== 1. 创建测试用户 ==========
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'password': 'test123456'}  # 密码会自动哈希，不用手动处理
    )
    if created:
        user.set_password('test123456')  # 确保密码是哈希后的
        user.save()
    print(f"用户创建/获取成功：{user.username}")

    # ========== 2. 创建分类数据（修复get_or_create，一次性传所有字段） ==========
    categories = [
        {'name': 'Study', 'color': '#4CAF50', 'description': '学习相关任务'},
        {'name': 'Work', 'color': '#2196F3', 'description': '工作相关任务'},
        {'name': 'Life', 'color': '#FFC107', 'description': '生活相关任务'}
    ]
    cat_dict = {}
    for cat in categories:
        # 关键：get_or_create的defaults传所有非默认字段，避免空值
        c, created = Category.objects.get_or_create(
            name=cat['name'],  # 唯一标识字段
            defaults={
                'color': cat['color'],
                'description': cat['description']
            }
        )
        cat_dict[cat['name']] = c
        print(f"分类{'创建' if created else '获取'}成功：{c.name}")

    # ========== 3. 创建优先级数据（核心修复：rank_order传入defaults） ==========
    priorities = [
        {'level': 'High', 'rank_order': 3},
        {'level': 'Medium', 'rank_order': 2},
        {'level': 'Low', 'rank_order': 1}
    ]
    prio_dict = {}
    for prio in priorities:
        # 关键：把rank_order放到defaults里，确保创建时自动赋值
        p, created = Priority.objects.get_or_create(
            level=prio['level'],  # 唯一标识字段
            defaults={'rank_order': prio['rank_order']}  # 非空字段必须传
        )
        prio_dict[prio['level']] = p
        print(f"优先级{'创建' if created else '获取'}成功：{p.level} (rank: {p.rank_order})")

    # ========== 4. 创建测试任务 ==========
    tasks = [
        {
            'title': '完成Django项目搭建',
            'description': '实现任务创建、编辑、删除功能',
            'due_date': date.today() + timedelta(days=1),
            'category': cat_dict['Study'],
            'priority': prio_dict['High'],
            'status': False
        },
        {
            'title': '学习Django模板继承',
            'description': '掌握模板继承知识，优化页面结构',
            'due_date': date.today() + timedelta(days=3),
            'category': cat_dict['Study'],
            'priority': prio_dict['Medium'],
            'status': False
        },
        {
            'title': '买 groceries',
            'description': '购买牛奶、面包、蔬菜',
            'due_date': date.today(),
            'category': cat_dict['Life'],
            'priority': prio_dict['Low'],
            'status': True
        }
    ]

    for t in tasks:
        task, created = Task.objects.get_or_create(
            user=user,
            title=t['title'],  # 唯一标识（避免重复创建）
            defaults={
                'description': t['description'],
                'due_date': t['due_date'],
                'category': t['category'],
                'priority': t['priority'],
                'status': t['status']
            }
        )
        print(f"任务{'创建' if created else '获取'}成功：{task.title}")

    # ========== 5. 打印最终数据 ==========
    print("\n===== 测试数据填充完成！=====")
    for task in Task.objects.filter(user=user):
        print(f"- {task.title} | 分类：{task.category.name} | 优先级：{task.priority.level} | 状态：{'已完成' if task.status else '未完成'}")

if __name__ == '__main__':
    print("开始填充测试数据...\n")
    populate()
    print("\n===== 所有操作完成！=====")