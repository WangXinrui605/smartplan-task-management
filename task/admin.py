from django.contrib import admin
from .models import Category, Task

# Custom admin configuration to improve usability for task management
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'due_date', 'status', 'created_at')  
    list_filter = ('category', 'priority', 'status', 'due_date')  
    search_fields = ('title', 'description')  


admin.site.register(Category)
admin.site.register(Task, TaskAdmin)