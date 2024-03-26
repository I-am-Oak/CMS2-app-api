from django.shortcuts import render
from django.views.generic import TemplateView

class page(TemplateView):
    template_name = 'index.html'


class LoginPageView(TemplateView):
    template_name = 'login.html'


def home_view(request):
    return render(request, 'home.html')