from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Task, Category
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from django.db.models import Case, When, IntegerField

def register_view(request):
    if request.user.is_authenticated:
        return redirect('task_dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task_dashboard')
    else:
        form = UserCreationForm()

    return render(request, 'task/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('task_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('task_dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'task/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

def get_current_user(request):
    return User.objects.get(username='testuser')


# 1. 任务仪表盘（只负责任务列表和操作）
@login_required
def task_dashboard(request):
    user = request.user

    """处理排序（下拉框传的sort）"""
    sort_by = request.GET.get('sort', 'due_date')#默认按截止日期排序
    query = request.GET.get('q', '').strip()
    period = request.GET.get('period', 'all')

    tasks = Task.objects.filter(user=user)

    # search: title or contains key word
    if query:
        tasks= tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if sort_by == 'priority':
        tasks = tasks.annotate(
            priority_order=Case(
                When(priority='high', then=3),
                When(priority='medium', then=2),
                When(priority='low', then=1),
                default=0,
                output_field=IntegerField()
            )
        ).order_by('-priority_order')#优先级
    elif sort_by == 'created_at':
        tasks = tasks.order_by('-created_at')#创建时间
    else:
        tasks = tasks.order_by('due_date')#截止日期

    today = timezone.localdate()

    # 根据 period 决定当前表格显示哪些任务
    if period == 'today':
        tasks = tasks.filter(due_date=today, status=False)
        period_title = 'Today'
    elif period == 'future':
        tasks = tasks.filter(due_date__gt=today, status=False)
        period_title = 'Future'
    elif period == 'history':
        tasks = tasks.filter(Q(status=True) | Q(due_date__lt=today))
        period_title = 'History'
    else:
        period_title = 'All Tasks'

    categories = Category.objects.all()


#模板需要的数据
    context = {
        'tasks': tasks,
        'categories': categories,
        'current_sort': sort_by,
        'current_query': query,
        'current_period': period,
        'period_title': period_title,
        'user': user
    }
    return render(request, 'task/dashboard.html', context)


# 2. 统计页面（只负责统计数据）
@login_required
def stats_page(request):
    user = request.user

    range_filter = request.GET.get('range', 'all')  # week / month / all
    today = timezone.localdate()

    # 第一步：查询当前用户的所有任务
    tasks = Task.objects.filter(user=user)

    # 按时间范围筛选（这里先按 created_at 来算）
    if range_filter == 'week':
        start_date = today - timedelta(days=today.weekday())  # 本周周一
        tasks = tasks.filter(created_at__date__gte=start_date)
        range_label = 'This Week'
    elif range_filter == 'month':
        start_date = today.replace(day=1)  # 本月1号
        tasks = tasks.filter(created_at__date__gte=start_date)
        range_label = 'This Month'
    else:
        range_label = 'All Time'

    # 第二步：计算统计数据
    total_tasks = tasks.count()#总任务数
    completed_tasks = tasks.filter(status=True).count()#已完成任务数
    incomplete_tasks = total_tasks - completed_tasks
    #完成率
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    completed_pct=round(completion_rate)
    pending_pct=100 - completed_pct if total_tasks > 0 else 0

    # 分类统计（柱状图）
    category_stats = []
    categories = Category.objects.all()

    max_category_count = 0
    temp_stats = []

    for cat in categories:
        count = tasks.filter(category=cat).count()
        temp_stats.append({
            'name': cat.name,
            'count': count,
        })
        if count > max_category_count:
            max_category_count = count

    for stat in temp_stats:
        if max_category_count > 0:
            height_pct = int((stat['count'] / max_category_count) * 100)
        else:
            height_pct = 0

        category_stats.append({
            'name': stat['name'],
            'count': stat['count'],
            'height_pct': height_pct
        })
    # 第三步：准备模板数据
    context = {
        'range_filter': range_filter,
        'range_label': range_label,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'incomplete_tasks': incomplete_tasks,
        'completion_rate': round(completion_rate, 1),# 保留1位小数
        'completed_pct': completed_pct,
        'pending_pct': pending_pct,
        'category_stats': category_stats,
        'user': user
    }
    return render(request, 'task/stats.html', context)

# 3. 创建任务
@login_required
def create_task(request):
    user = request.user
    categories = Category.objects.all()
    errors = []
    # 第一步：处理POST请求（用户提交表单）
    if request.method == 'POST':
        # 获取表单数据
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date') or None
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
            category = Category.objects.filter(id=category_id).first() if category_id else None
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
@login_required
def edit_task(request, task_id):
    user = request.user
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
            task.category = Category.objects.filter(id=category_id).first() if category_id else None
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
@login_required
def delete_task(request, task_id):
    user = request.user
    task = get_object_or_404(Task, id=task_id, user=user)
    task.delete()#删除任务
    return redirect('task_dashboard')#重定向到仪表盘


# 6. 切换任务状态
@login_required
def toggle_task_status(request, task_id):
    user = request.user
    task = get_object_or_404(Task, id=task_id, user=user)
    task.status = not task.status
    task.completed_at = timezone.now() if task.status else None
    task.save()
    return redirect('task_dashboard')

