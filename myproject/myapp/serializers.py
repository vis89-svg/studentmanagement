from rest_framework import serializers
from .models import StudentRegistration

class StudentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentRegistration
        fields = ['id', 'username', 'name', 'password', 'class_name', 'admission_date', 'age', 'email']

