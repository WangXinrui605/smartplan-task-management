from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User  # 复用Django默认用户模型（避免重复开发）

class Category(models.Model):
    """任务分类模型（Study/Work/Life）"""
    name = models.CharField(max_length=100, unique=True)  # 分类名称
    color = models.CharField(max_length=7, default='#000000')  # 颜色（如#FF0000）
    description = models.TextField(blank=True)  # 分类描述（可选）

    def __str__(self):
        return self.name  # Admin显示分类名称

#Priority 改为 Task 的一个简单属性
# class Priority(models.Model):
#     """优先级模型（High/Medium/Low）"""
#     level = models.CharField(max_length=50, unique=True)  # 优先级等级（High/Medium/Low）
#     rank_order = models.IntegerField(unique=True)  # 排序权重（如3=High，2=Medium，1=Low）
#
#     def __str__(self):
#         return self.level #后台显示优先级

class Task(models.Model):
    """任务模型（核心模型）"""
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 关联用户（一对多）
    title = models.CharField(max_length=255)  # 任务标题（必填）
    description = models.TextField(blank=True)  # 任务描述（可选）
    due_date = models.DateField(null=True, blank=True)  # 截止日期（可选）
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间（自动填充）
    completed_at = models.DateTimeField(null=True, blank=True)  # 完成时间（可选）
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,blank=True)  # 关联分类
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')  # 关联优先级
    status = models.BooleanField(default=False)  # 完成状态（默认未完成）

    def __str__(self):
        return self.title  # Admin显示任务标题