from django.forms import ModelForm, TextInput
from django import forms
from .models import ChatMessage


class ChatMessageForm(ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['body']
        widgets = {
            'body': TextInput(attrs={
                'placeholder': 'Add message ...',
                'class': 'form-control',
            })
        }