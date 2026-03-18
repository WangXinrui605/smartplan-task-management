from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User  

# Category model represents logical grouping of tasks (e.g., Study, Work, Life)
# This allows filtering, statistics, and better organisation of tasks
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  
    color = models.CharField(max_length=7, default='#000000')  
    description = models.TextField(blank=True)  

    def __str__(self):
# Return human-readable name for admin interface
        return self.name 



class Task(models.Model):
    """
    Core model representing a user task.

    Design decision:
    - Priority is implemented as a simple choice field instead of a separate model,
      as the system only requires fixed levels (High, Medium, Low).
    """
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

# Each task is associated with a user to ensure data isolation
    user = models.ForeignKey(User, on_delete=models.CASCADE)
# Basic task information
    title = models.CharField(max_length=255) 
    description = models.TextField(blank=True) 
# Optional scheduling fields
    due_date = models.DateField(null=True, blank=True) 
# Automatically track creation and completion timestamps
    created_at = models.DateTimeField(auto_now_add=True)  
    completed_at = models.DateTimeField(null=True, blank=True)  
# Optional category for filtering and statistics
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True,blank=True) 
# Priority stored as a lightweight attribute for performance and simplicity
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')  
# Boolean status for quick filtering (completed / incomplete)
    status = models.BooleanField(default=False) 
# Optional note for additional task details (used in preview modal)
    note = models.TextField(blank=True, null=True) 

    def __str__(self):
# Used in admin and debugging for quick identification
        return self.title  