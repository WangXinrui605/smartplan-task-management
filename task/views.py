from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import Task, Category
from datetime import date
from django.utils import timezone


def get_current_user(request):
    return User.objects.get(username='testuser')


# 1. 任务仪表盘（只负责任务列表和操作）
def task_dashboard(request):
    user = get_current_user(request)#获取用户

    """处理排序（下拉框传的sort）"""
    sort_by = request.GET.get('sort', 'due_date')#默认按截止日期排序

    if sort_by == 'priority':
        tasks = Task.objects.filter(user=user).order_by('-priority')#优先级
    elif sort_by == 'created_at':
        tasks = Task.objects.filter(user=user).order_by('-created_at')#创建时间
    else:
        tasks = Task.objects.filter(user=user).order_by('due_date')#截止日期

    categories = Category.objects.all()


#模板需要的数据
    context = {
        'tasks': tasks,
        'categories': categories,
        'current_sort': sort_by,
        'user': user
    }
    return render(request, 'task/dashboard.html', context)


# 2. 统计页面（只负责统计数据）
def stats_page(request):
    user = get_current_user(request)
    # 第一步：查询当前用户的所有任务
    tasks = Task.objects.filter(user=user)
    # 第二步：计算统计数据
    total_tasks = tasks.count()#总任务数
    completed_tasks = tasks.filter(status=True).count()#已完成任务数
    #完成率
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0

    # 按分类统计
    category_stats = []
    for cat in Category.objects.all():
        cat_tasks = tasks.filter(category=cat)
        category_stats.append({
            'name': cat.name,
            'count': cat_tasks.count(),
            'completed': cat_tasks.filter(status=True).count()
        })

    # 按优先级统计
    priority_stats = []
    priority_choices = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    for value, label in priority_choices:
        prio_tasks = tasks.filter(priority=value)
        priority_stats.append({
            'level': label,
            'count': prio_tasks.count(),
            'completed': prio_tasks.filter(status=True).count()
        })
    # 第三步：准备模板数据
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),# 保留1位小数
        'category_stats': category_stats,
        'priority_stats': priority_stats,
        'user': user
    }
    return render(request, 'task/stats.html', context)


# 3. 创建任务
def create_task(request):
    user = get_current_user(request)
    categories = Category.objects.all()
    errors = []
    # 第一步：处理POST请求（用户提交表单）
    if request.method == 'POST':
        # 获取表单数据
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        category_id = request.POST.get('category')
        priority = request.POST.get('priority','medium')
        note=request.POST.get('note')

        # 表单验证（M4需求）
        if not title:
            errors.append('任务标题不能为空！')
        if due_date and due_date < date.today().isoformat():
            errors.append('截止日期不能早于今天！')

        if not errors:
            # 创建任务
            category = Category.objects.get(id=category_id) if category_id else None
            Task.objects.create(
                user=user,
                title=title,
                description=description,
                due_date=due_date if due_date else None,
                category=category,
                priority=priority,
                note=note
            )
            return redirect('task_dashboard')  # 跳转回仪表盘

    context = {
        'categories': categories,
        'errors': errors,
        'user': user
    }
    return render(request, 'task/create_task.html', context)


# 4. 编辑任务
def edit_task(request, task_id):
    user = get_current_user(request)
    task = get_object_or_404(Task, id=task_id, user=user)  # 确保任务属于当前用户
    categories = Category.objects.all()
    errors = []

    if request.method == 'POST':
        #更新任务数据
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        category_id = request.POST.get('category')
        priority = request.POST.get('priority','medium')
        status = request.POST.get('status') == 'on'  # 复选框值处理
        note = request.POST.get('note')

        # 表单验证
        if not title:
            errors.append('任务标题不能为空！')
        if due_date and due_date < date.today().isoformat():
            errors.append('截止日期不能早于今天！')

        if not errors:
            # 更新任务
            task.title = title
            task.description = description
            task.due_date = due_date if due_date else None
            task.category = Category.objects.get(id=category_id) if category_id else None
            task.priority = priority
            task.status = status
            task.note = note
            # 如果标记为完成，设置completed_at
            if status and not task.completed_at:
                task.completed_at = timezone.now()
            elif not status:#如果用户把一个已完成任务改回未完成，completed_at 应该清空
                task.completed_at = None
            task.save()
            return redirect('task_dashboard')

    context = {
        'task': task,
        'categories': categories,
        'errors': errors,
        'user': user
    }
    return render(request, 'task/edit_task.html', context)


# 5. 删除任务
def delete_task(request, task_id):
    user = get_current_user(request)
    task = get_object_or_404(Task, id=task_id, user=user)
    task.delete()#删除任务
    return redirect('task_dashboard')#重定向到仪表盘


# 6. 切换任务状态
def toggle_task_status(request, task_id):
    user = get_current_user(request)
    task = get_object_or_404(Task, id=task_id, user=user)
    task.status = not task.status
    task.completed_at = timezone.now() if task.status else None
    task.save()
    return redirect('task_dashboard')

