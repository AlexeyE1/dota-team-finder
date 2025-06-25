from django.contrib.auth.views import LogoutView
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from .models import CustomUser
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django import forms


class ProfileEditInlineForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['steam_nickname', 'bio', 'role', 'available_from', 'available_to']

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('main:main')


class ProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'profile.html'
    context_object_name = 'profile'


    def get_object(self):
        if not self.kwargs.get('slug_profile'):
            user = self.request.user
            return user
        return get_object_or_404(CustomUser, slug=self.kwargs['slug_profile'])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Редактирование доступно только владельцу профиля
        edit_mode = request.GET.get('edit') == '1' and request.user == self.object
        form = ProfileEditInlineForm(instance=self.object) if edit_mode else None
        context = self.get_context_data(object=self.object, form=form, edit_mode=edit_mode)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # POST-запросы доступны только владельцу профиля
        if request.user != self.object:
            return HttpResponseForbidden()
        form = ProfileEditInlineForm(request.POST, instance=self.object)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(self.request.path)
        context = self.get_context_data(object=self.object, form=form, edit_mode=True)
        return self.render_to_response(context)