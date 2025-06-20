from django.shortcuts import render
from django.views.generic import TemplateView
import requests



class HomeView(TemplateView):
    template_name = 'main/home.html'
