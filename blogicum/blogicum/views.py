from django.contrib.auth import logout as auth_logout
from django.shortcuts import render


def blogicum_logout(request):
    auth_logout(request)
    return render(request, 'registration/logged_out.html')
