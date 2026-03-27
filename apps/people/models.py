from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Person(models.Model):
    """Model representing a user profile."""

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="person")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
