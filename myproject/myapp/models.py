from django.db import models
import datetime
from django.utils import timezone
# Create your models here.

class StudentRegistration(models.Model):
    username = models.CharField(max_length=100)
    name = models.CharField(max_length=100,null = True)
    password = models.CharField(max_length=100)
    class_name = models.CharField(max_length=100)
    admission_date = models.DateField()
    age = models.IntegerField()
    email = models.EmailField()

    def __str__(self):
        return self.username