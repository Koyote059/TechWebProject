import os

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView

from GymApp.forms import UserRegistrationForm
from GymApp.models import GymUser, Mail
from GymApp.settings import MEDIA_ROOT


class MailForm(forms.ModelForm):
    class Meta:
        model = Mail
        fields = ['email', 'title', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'title': forms.TextInput(attrs={'placeholder': 'Titolo'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Scrivi un messaggio...'}),
        }


class HomePageView(CreateView):
    model = Mail
    form_class = MailForm
    template_name = 'home.html'
    success_url = reverse_lazy('home')


class UserDetailView(LoginRequiredMixin, DetailView):
    model = GymUser
    template_name = 'user.html'
    context_object_name = 'user'

    def get_object(self, queryset=None):
        return self.request.user


class UserEditForm(forms.ModelForm):
    class Meta:
        model = GymUser
        fields = ['username', 'first_name', 'last_name', 'email', 'weight', 'height', 'date_of_birth', 'picture']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'picture': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean_picture(self):
        if 'picture' not in self.cleaned_data or self.cleaned_data['picture'] is None:
            return None
        picture = self.cleaned_data['picture']
        if picture:
            if picture.size > 2 * 400 * 400:
                raise forms.ValidationError("Image file too large ( > 2mb )")
            return picture
        else:
            raise forms.ValidationError("Couldn't read uploaded image")


class UserEditView(LoginRequiredMixin, UpdateView):
    form_class = UserEditForm
    model = GymUser
    template_name = 'edit_profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def post(self, request, *args, **kwargs):
        if 'picture' in request.FILES and request.FILES['picture']:
            request.FILES['picture'].name = self.request.user.username + '.jpg'
            media_path = MEDIA_ROOT + "/" + GymUser.picture.field.upload_to + "/" + self.request.user.username + '.jpg'
            if os.path.exists(media_path):
                os.remove(media_path)
        return super().post(request, *args, **kwargs)


def handler_404(request, exception):
    return render(request, '404.html', status=404)
