# Create your views here.
from django.contrib import messages
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView
from django.views.generic import *
from django.views.generic.base import View, ContextMixin

from Quizzes_Surveys.decorators import student_required, teacher_required
from quiz.models import Quiz
from users.models import User, Student, Subject, Teacher, Batch
from .forms import StudentRegisterForm, TeacherRegisterForm


class RegisterStudentView(SuccessMessageMixin, CreateView):
    model = User
    form_class = StudentRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')
    success_message = "Account for %(username)s created, you can login now"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, username=self.object.username, )

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)


class RegisterTeacherView(SuccessMessageMixin, CreateView):
    model = User
    form_class = TeacherRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')
    success_message = "Account for %(username)s created, you can login now"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data, username=self.object.username, )

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)


@method_decorator([login_required, student_required], name='dispatch')
class StudentQuizListView(UserPassesTestMixin, ListView, ContextMixin):
    template_name = 'users/quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        self.user = get_object_or_404(User, pk=self.kwargs['pk'])
        quiz_set = Quiz.objects.filter(batches__student=self.user.student).order_by('subject__name')
        return quiz_set

    def get_subject_list(self):
        subject_list = []
        for quiz in Quiz.objects.filter(batches__student=self.user.student).order_by('subject__name'):
            subject = quiz.subject.name
            if subject not in subject_list:
                subject_list.append(subject)
        return subject_list

    def get_subject_with_open_quiz_list(self):
        subject_list = []
        for quiz in Quiz.objects.filter(batches__student=self.user.student).order_by('subject__name'):
            if quiz.is_open:
                subject = quiz.subject.name
                if subject not in subject_list:
                    subject_list.append(subject)
        return subject_list

    def get_subject_with_close_quiz_list(self):
        subject_list = []
        for quiz in Quiz.objects.filter(batches__student=self.user.student).order_by('subject__name'):
            if not quiz.is_open:
                subject = quiz.subject.name
                if subject not in subject_list:
                    subject_list.append(subject)
        return subject_list

    def test_func(self):
        return self.kwargs['pk'] == self.request.user.pk


@method_decorator([login_required, teacher_required], name='dispatch')
class TeacherSubjectListView(UserPassesTestMixin, ListView):
    template_name = 'users/quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        self.user = get_object_or_404(User, pk=self.kwargs['pk'])
        subjects = self.user.teacher.subjects.all()
        quiz_set = Quiz.objects.filter(subject__in=subjects).order_by('subject__name')
        return quiz_set

    def get_subject_list(self):
        subject_list = []
        self.user = get_object_or_404(User, pk=self.kwargs['pk'])
        subjects = self.user.teacher.subjects.all()
        for quiz in Quiz.objects.filter(subject__in=subjects).order_by('subject__name'):
            subject = quiz.subject.name
            if subject not in subject_list:
                subject_list.append(subject)
        subject_list.sort()
        return subject_list

    def get_my_subject_list(self):
        subject_list = []
        for quiz in Quiz.objects.filter(author=self.user.teacher).order_by('subject__name'):
                subject = quiz.subject.name
                if subject not in subject_list:
                    subject_list.append(subject)
        return subject_list

    def test_func(self):
        return self.kwargs['pk'] == self.request.user.pk


class LoginView(View):

    def get(self, request):
        if self.request.user.is_authenticated:
            if self.request.user.is_teacher:
                return redirect('teacher-home', pk=self.request.user.pk)
            else:
                return redirect('student-home', pk=self.request.user.pk)
        return render(request, 'users/login.html', {'form': AuthenticationForm()})

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active and not user.is_teacher:
                login(request, user)
                return redirect('student-home', pk=user.pk)
            elif user.is_active and user.is_teacher:
                login(request, user)
                return redirect('teacher-home', pk=user.pk)

        return redirect('login')


class UserUpdateView(UpdateView):
    model = User
    template_name = 'users/update_profile.html'
    fields = ['first_name', 'last_name', 'email']

    def get_success_url(self):
        user = self.get_object()
        if user.is_teacher:
            return reverse_lazy('teacher-home', kwargs={'pk': user.pk})
        else:
            return reverse_lazy('student-home', kwargs={'pk': user.pk})


class TeacherProfileView(DetailView):
    model = Teacher
    template_name = 'users/user_detail.html'


class StudentProfileView(DetailView):
    model = Student
    template_name = 'users/user_detail.html'


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {
        'form': form
    })
