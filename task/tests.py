from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Task, Category

# Unit tests for Task model and dashboard view
# Ensures core functionality behaves as expected
class TaskModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="anna", password="123456")
        self.category = Category.objects.create(name="Work")

    def test_create_task(self):
        task = Task.objects.create(
            user=self.user,
            title="Finish report",
            description="Write implementation",
            category=self.category,
            priority="high",
            status=False
        )

        self.assertEqual(task.title, "Finish report")
        self.assertEqual(task.priority, "high")
        self.assertEqual(task.user.username, "anna")
        self.assertEqual(task.category.name, "Work")

    def test_default_priority(self):
        task = Task.objects.create(
            user=self.user,
            title="Default priority task"
        )

        self.assertEqual(task.priority, "medium")

    def test_str_method(self):
        task = Task.objects.create(
            user=self.user,
            title="Test Task"
        )

        self.assertEqual(str(task), "Test Task")


class DashboardViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="anna", password="123456")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("task_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_dashboard_logged_in(self):
        self.client.login(username="anna", password="123456")
        response = self.client.get(reverse("task_dashboard"))
        self.assertEqual(response.status_code, 200)