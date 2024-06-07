from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.sessions.models import Session

# Create your views here.

def home(request):
    return HttpResponse("Hello, World!")
