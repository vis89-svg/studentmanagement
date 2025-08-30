from rest_framework.views import APIView
from rest_framework.response import Response 
from rest_framework import status
from django.contrib.auth import authenticate, login  # (left as-is)
from django.shortcuts import get_object_or_404, render ,redirect
from .models import StudentRegistration
from .serializers import StudentRegistrationSerializer
from Exam.models import Exam
from Exam.serializers import ExamSerializer, ExamResponseSerializer
from Exam.models import ExamResponse
from django.contrib import messages

class StudentRegistrationView(APIView):
    template_name = "student_registration.html"

    def get(self, request):
        # If browser requests HTML, render template; otherwise return JSON as before
        if "text/html" in request.META.get("HTTP_ACCEPT", ""):
            return render(request, self.template_name)

        students = StudentRegistration.objects.all()
        serializer = StudentRegistrationSerializer(students, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Registration successful! Please login now.")
            return redirect("login")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.contrib.auth.models import User

class LoginAPIView(APIView):
    template_name = "login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # 1️⃣ Check Django superuser (default User model)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # set session
            if user.is_superuser:
                request.session['superuser'] = 'admin'
                return redirect("admin_profile")
            # Normal Django user (if any)
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            return redirect("profile")

        # 2️⃣ Check StudentRegistration (custom student)
        try:
            student = StudentRegistration.objects.get(username=username, password=password)
        except StudentRegistration.DoesNotExist:
            return render(request, self.template_name, {"error": "Invalid credentials"})

        # Student login success
        request.session['user_id'] = student.id
        request.session['username'] = student.username
        return redirect("profile")


class ProfileAPIView(APIView):
    template_name = "profile.html"

    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            if "text/html" in request.META.get("HTTP_ACCEPT", ""):
                return render(request, self.template_name, {"error": "Unauthorized"})
            return Response({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = StudentRegistration.objects.get(id=user_id)
        except StudentRegistration.DoesNotExist:
            if "text/html" in request.META.get("HTTP_ACCEPT", ""):
                return render(request, self.template_name, {"error": "User not found"})
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        exams = Exam.objects.all()

        if "text/html" in request.META.get("HTTP_ACCEPT", ""):
            return render(request, self.template_name, {"user": user, "exams": exams})

        user_data = StudentRegistrationSerializer(user).data
        exam_data = ExamSerializer(exams, many=True).data
        return Response({"user": user_data, "exams": exam_data}, status=status.HTTP_200_OK)

    def post(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect("login")  

          #exam display , (3rd time)
          
        exam_id = request.POST.get("exam_id")
        accepted = request.POST.get("accepted")

        if not exam_id or accepted not in ["true", "false"]:
            messages.error(request, "Invalid exam action.")
            return redirect("profile")

        try:
            student = StudentRegistration.objects.get(id=user_id)
            exam = Exam.objects.get(id=exam_id)
        except (StudentRegistration.DoesNotExist, Exam.DoesNotExist):
            messages.error(request, "Student or exam not found.")
            return redirect("profile")

        
        accepted_bool = accepted == "true"

        
        ExamResponse.objects.update_or_create(
            student=student,
            exam=exam,
            defaults={"accepted": accepted_bool}
        )

        
        messages.success(request, f'Your response for "{exam.title}" has been recorded.')
        return redirect("profile")


class EditProfileAPIView(APIView):
   
    template_name = "edit_profile.html"

    def get_object(self, pk=None):
        
       
        if self.request.session.get("superuser") == "admin" and pk is not None:
            return get_object_or_404(StudentRegistration, id=pk)

    
        user_id = self.request.session.get("user_id")
        if not user_id:
            return None
        return get_object_or_404(StudentRegistration, id=user_id)

    
    def get(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        profile = self.get_object(pk)

        if not profile:
            return render(request, self.template_name, {"error": "Profile not found"})

        return render(request, self.template_name, {"student": profile})

    
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk")
        profile = self.get_object(pk)

        if not profile:
            return render(request, self.template_name, {"error": "Profile not found"})

        serializer = StudentRegistrationSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("admin_profile" if request.session.get("superuser") == "admin" else "profile")

        return render(request, self.template_name, {"student": profile, "errors": serializer.errors})


class DeleteStudentAPIView(APIView):
    template_name = "delete_profile.html"

    def get(self, request, pk):
        student = get_object_or_404(StudentRegistration, pk=pk)
        return render(request, self.template_name, {"student": student})

    def post(self, request, pk):
       
        student = get_object_or_404(StudentRegistration, pk=pk)
        student.delete()
        messages.success(request, "Student profile deleted successfully.")
        return redirect("admin_profile")




class AdminProfileAPIView(APIView):
    template_name = "admin_profile.html"

    def get(self, request):
        
        if request.session.get("superuser") != "admin":
            
            return render(request, self.template_name, {"students": []})

        
        all_students = StudentRegistration.objects.all()
        return render(request, self.template_name, {"students": all_students})



class ForgotPasswordView(APIView):
    template_name = "forgot_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

       
        student = StudentRegistration.objects.filter(username=username).first()
        if not student:
            return render(request, self.template_name, {"error": "No account found with this username."})

        
        if new_password != confirm_password:
            return render(request, self.template_name, {"error": "Passwords do not match."})

       
        student.password = new_password
        student.save()
        messages.success(request, "Password updated successfully! Please login now.")

        return redirect("login")



class LogoutView(APIView):
    def get(self, request):
        request.session.flush() 
        return redirect("login")