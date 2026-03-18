from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Task, Category
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Q
from django.db.models import Case, When, IntegerField
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json


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


# Main dashboard view for displaying and managing user tasks
# Supports filtering, searching, and sorting via GET parameters
@login_required
def task_dashboard(request):
    user = request.user

    sort_by = request.GET.get('sort', 'due_date')
    query = request.GET.get('q', '').strip()
    period = request.GET.get('period', 'all')
    status_filter = request.GET.get('status', '').strip().lower()
    category_filter = request.GET.get('category', '').strip()
    priority_filter = request.GET.get('priority', '').strip().lower()

    tasks = Task.objects.filter(user=user)# Ensure users can only access their own tasks (data isolation)

# Allow flexible search across title and description fields
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    today = timezone.localdate()
    soon_limit = today + timedelta(days=3)
# Filter tasks based on time period to improve task organisation
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

    if status_filter == 'completed':
        tasks = tasks.filter(status=True)
    elif status_filter == 'pending':
        tasks = tasks.filter(status=False)
    elif status_filter == 'soon':
        tasks = tasks.filter(
            status=False,
            due_date__isnull=False,
            due_date__gte=today,
            due_date__lte=soon_limit
        )
    elif status_filter == 'overdue':
        tasks = tasks.filter(
            status=False,
            due_date__isnull=False,
            due_date__lt=today
        )

    if category_filter:
        tasks = tasks.filter(category__name=category_filter)

# Custom ordering is used to prioritise high-priority tasks first
# since priority is stored as text instead of numeric value
    if priority_filter in ['high', 'medium', 'low']:
        tasks = tasks.filter(priority=priority_filter)

    if sort_by == 'priority':
        tasks = tasks.annotate(
            priority_order=Case(
                When(priority='high', then=3),
                When(priority='medium', then=2),
                When(priority='low', then=1),
                default=0,
                output_field=IntegerField()
            )
        ).order_by('status', '-priority_order', 'due_date', '-created_at')
    elif sort_by == 'created_at':
        tasks = tasks.order_by('status', '-created_at')
    else:
        tasks = tasks.order_by('status', 'due_date', '-created_at')

# Compute additional display properties (not stored in DB)
# to simplify template logic and improve readability
    display_tasks = []
    for task in tasks:
        due_state = ''
        due_label = ''
        history_state = ''

        if task.due_date:
            if not task.status and task.due_date < today:
                due_state = 'overdue'
                due_label = 'Overdue'
            elif not task.status and task.due_date == today:
                due_state = 'today'
                due_label = 'Today'
            elif not task.status and task.due_date == today + timedelta(days=1):
                due_state = 'tomorrow'
                due_label = 'Tomorrow'
            elif not task.status and task.due_date <= soon_limit:
                due_state = 'upcoming'
                due_label = 'Upcoming'
            elif not task.status and task.due_date > soon_limit:
                due_state = 'upcoming'
                due_label = 'Upcoming'
            elif task.status:
                due_state = 'done'
                due_label = 'Completed'

        if period == 'history':
            if task.status:
                history_state = 'completed'
            elif task.due_date and task.due_date < today:
                history_state = 'overdue'

        task.due_state = due_state
        task.due_label = due_label
        task.history_state = history_state
        display_tasks.append(task)

    categories = Category.objects.all()

    context = {
        'tasks': display_tasks,
        'categories': categories,
        'current_sort': sort_by,
        'current_query': query,
        'current_period': period,
        'current_status_filter': status_filter,
        'current_category_filter': category_filter,
        'current_priority_filter': priority_filter,
        'period_title': period_title,
        'today': today,
        'user': user
    }
    return render(request, 'task/dashboard.html', context)

# Generate task statistics for visualisation (charts and summaries)
# Includes completion rate, category distribution, and priority breakdown
@login_required
def stats_page(request):
    user = request.user

    range_filter = request.GET.get('range', 'all')
    today = timezone.localdate()
    soon_limit = today + timedelta(days=3)

    tasks = Task.objects.filter(user=user)

    if range_filter == 'week':
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        tasks = tasks.filter(due_date__range=[week_start, week_end])
        range_label = 'Due This Week'
    elif range_filter == 'month':
        month_start = today.replace(day=1)
        if month_start.month == 12:
            next_month_start = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            next_month_start = month_start.replace(month=month_start.month + 1, day=1)
        month_end = next_month_start - timedelta(days=1)
        tasks = tasks.filter(due_date__range=[month_start, month_end])
        range_label = 'Due This Month'
    else:
        range_label = 'All Tasks'

    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status=True).count()
    incomplete_tasks = tasks.filter(status=False).count()

    due_soon_tasks = tasks.filter(
        status=False,
        due_date__isnull=False,
        due_date__gte=today,
        due_date__lte=soon_limit
    ).count()

    completion_rate = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0

    max_status_count = max(completed_tasks, incomplete_tasks, due_soon_tasks) if total_tasks > 0 else 0

    if max_status_count > 0:
        completed_bar_pct = int((completed_tasks / max_status_count) * 100)
        pending_bar_pct = int((incomplete_tasks / max_status_count) * 100)
        soon_bar_pct = int((due_soon_tasks / max_status_count) * 100)
    else:
        completed_bar_pct = 0
        pending_bar_pct = 0
        soon_bar_pct = 0

    study_count = tasks.filter(category__name='Study').count()
    work_count = tasks.filter(category__name='Work').count()
    life_count = tasks.filter(category__name='Life').count()

    high_priority_count = tasks.filter(priority='high').count()
    medium_priority_count = tasks.filter(priority='medium').count()
    low_priority_count = tasks.filter(priority='low').count()

    circumference = 490.09

    if total_tasks > 0:
        study_len = round((study_count / total_tasks) * circumference, 2)
        work_len = round((work_count / total_tasks) * circumference, 2)
        life_len = round((life_count / total_tasks) * circumference, 2)
    else:
        study_len = 0
        work_len = 0
        life_len = 0

    study_offset = 0
    work_offset = -study_len
    life_offset = -(study_len + work_len)

    category_stats = [
        {'name': 'Study', 'count': study_count},
        {'name': 'Work', 'count': work_count},
        {'name': 'Life', 'count': life_count},
    ]

    context = {
        'range_filter': range_filter,
        'range_label': range_label,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'incomplete_tasks': incomplete_tasks,
        'due_soon_tasks': due_soon_tasks,
        'completion_rate': completion_rate,
        'max_status_count': max_status_count,
        'completed_bar_pct': completed_bar_pct,
        'pending_bar_pct': pending_bar_pct,
        'soon_bar_pct': soon_bar_pct,
        'category_stats': category_stats,
        'study_count': study_count,
        'work_count': work_count,
        'life_count': life_count,
        'study_len': study_len,
        'work_len': work_len,
        'life_len': life_len,
        'study_offset': study_offset,
        'work_offset': work_offset,
        'life_offset': life_offset,
        'high_priority_count': high_priority_count,
        'medium_priority_count': medium_priority_count,
        'low_priority_count': low_priority_count,
        'user': user
    }
    return render(request, 'task/stats.html', context)

# Handle task creation with basic validation
# Validation ensures meaningful data and prevents invalid dates
@login_required
def create_task(request):
    user = request.user
    categories = Category.objects.all()
    errors = []

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date') or None
        category_id = request.POST.get('category')
        priority = request.POST.get('priority', 'medium')
        note = request.POST.get('note')

        if not title:
            errors.append('Task title cannot be empty.')
        if due_date and due_date < date.today().isoformat():
            errors.append('Due date cannot be earlier than today.')

        if not errors:
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
            return redirect('task_dashboard')

    context = {
        'categories': categories,
        'errors': errors,
        'user': user
    }
    return render(request, 'task/create_task.html', context)


@login_required
def edit_task(request, task_id):
    user = request.user
    task = get_object_or_404(Task, id=task_id, user=user)
    categories = Category.objects.all()
    errors = []

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date') or None
        category_id = request.POST.get('category')
        priority = request.POST.get('priority', 'medium')
        status = request.POST.get('status') == 'on'
        note = request.POST.get('note')

        if not title:
            errors.append('Task title cannot be empty.')

        # Editing is allowed even if the task is already overdue.
        # Allow users to update overdue tasks to maintain flexibility
        # Only validate the field format indirectly by saving the submitted value.

        if not errors:
            task.title = title
            task.description = description
            task.due_date = due_date if due_date else None
            task.category = Category.objects.filter(id=category_id).first() if category_id else None
            task.priority = priority
            task.status = status
            task.note = note

            if status and not task.completed_at:
                task.completed_at = timezone.now()
            elif not status:
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


@login_required
def delete_task(request, task_id):
    user = request.user
    task = get_object_or_404(Task, id=task_id, user=user)
    task.delete()
    return redirect('task_dashboard')


@login_required
def toggle_task_status(request, task_id):
    user = request.user
    task = get_object_or_404(Task, id=task_id, user=user)

    task.status = not task.status
    task.completed_at = timezone.now() if task.status else None
    task.save()

    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)

    return redirect('task_dashboard')

# Simple rule-based priority suggestion system
# Uses keyword matching instead of ML to keep implementation lightweight
# and interpretable for users
@require_POST
@login_required
def suggest_priority(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        title = (data.get("title") or "").strip()
        note = (data.get("note") or "").strip()
        text = f"{title} {note}".lower()

        if not title and not note:
            return JsonResponse({
                "success": True,
                "priority": "None",
                "reason": "No task title or note has been entered yet, so Smart cannot estimate the urgency level."
            })

# Keywords are grouped by urgency level to estimate task importance
        high_keywords = [
            "urgent", "asap", "immediately", "right now", "today", "tonight",
            "deadline", "due", "exam", "interview", "submission", "submit",
            "presentation", "meeting", "report due", "pay", "payment"
        ]

        medium_keywords = [
            "prepare", "review", "revise", "plan", "organise", "organize",
            "draft", "study", "assignment", "coursework", "project",
            "follow up", "follow-up", "schedule", "arrange"
        ]

        low_keywords = [
            "idea", "someday", "later", "optional", "maybe", "wishlist",
            "try", "explore", "read", "watch", "clean", "buy", "shopping"
        ]

        matched_high = [word for word in high_keywords if word in text]
        matched_medium = [word for word in medium_keywords if word in text]
        matched_low = [word for word in low_keywords if word in text]

        high_score = len(matched_high) * 3
        medium_score = len(matched_medium) * 2
        low_score = len(matched_low)

        if len(note) > 80:
            medium_score += 1

        if any(word in text for word in ["tomorrow", "this week", "soon"]):
            high_score += 2

        if any(word in text for word in ["next week", "later this week"]):
            medium_score += 2

        if any(word in text for word in ["whenever", "no rush", "not urgent"]):
            low_score += 2

        if high_score >= medium_score and high_score >= low_score and high_score > 0:
            priority = "High"
            if matched_high:
                reason = (
                    "This task appears time-sensitive or urgent based on the wording used, "
                    f"such as: {', '.join(matched_high[:3])}. "
                    "Smart recommends setting it to High priority so it can be handled as soon as possible."
                )
            else:
                reason = (
                    "This task seems urgent or close to an important deadline. "
                    "Smart recommends setting it to High priority so it stays visible and gets attention quickly."
                )
        elif medium_score >= low_score and medium_score > 0:
            priority = "Medium"
            if matched_medium:
                reason = (
                    "This task looks important but not immediately critical based on terms like "
                    f"{', '.join(matched_medium[:3])}. "
                    "Smart recommends Medium priority so it remains on your schedule without being treated as urgent."
                )
            else:
                reason = (
                    "This task seems meaningful and worth planning for, but it does not appear highly urgent. "
                    "Smart recommends Medium priority to keep it active and manageable."
                )
        else:
            priority = "Low"
            if matched_low:
                reason = (
                    "This task appears flexible or lower-pressure based on terms like "
                    f"{', '.join(matched_low[:3])}. "
                    "Smart recommends Low priority because it does not seem urgent at the moment."
                )
            else:
                reason = (
                    "No strong signs of urgency were found in the task title or note. "
                    "Smart recommends Low priority because this task appears safe to complete later."
                )

        return JsonResponse({
            "success": True,
            "priority": priority,
            "reason": reason
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=400)
