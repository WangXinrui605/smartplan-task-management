from django.contrib import admin
from .models import Category, Task

# 自定义Task Admin，方便管理任务
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'due_date', 'status', 'created_at')  # 列表显示字段
    list_filter = ('category', 'priority', 'status', 'due_date')  # 筛选器
    search_fields = ('title', 'description')  # 搜索框（按标题/描述搜索）

# 注册模型到Admin
admin.site.register(Category)
admin.site.register(Task, TaskAdmin)