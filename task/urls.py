# task/urls.py
from django.urls import path
from . import views  # 导入task应用的视图

# 定义task应用的URL模式
urlpatterns = [
    # 任务仪表盘（首页）
    path('', views.task_dashboard, name='task_dashboard'),
    # 统计页面
    path('stats/', views.stats_page, name='stats_page'),
    # 创建任务
    path('task/create/', views.create_task, name='create_task'),
    # 编辑任务（动态参数：任务ID）
    path('task/edit/<int:task_id>/', views.edit_task, name='edit_task'),
    # 删除任务
    path('task/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    # 切换任务状态（已完成/未完成）
    path('task/toggle/<int:task_id>/', views.toggle_task_status, name='toggle_task_status'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]