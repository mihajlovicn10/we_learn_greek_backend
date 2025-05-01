from django.shortcuts import render, redirect 
from django.contrib.auth.forms import UserCreationForm 
from django.contrib.auth import login 
from django.contrib import messages 
from .models import User 
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy 
from .forms import CustomUserCreationForm

def index_view(request): 
    return render(request, 'index.html') 

def register(request): 
    if request.method == 'POST': 
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid(): 
            user = form.save() 
            user.set_password(form.cleaned_data['password1'])
            user.save() 
            login(request, user) 
            messages.success(request, 'Your account has been created successfully!')
            return redirect('login')
        else: 
            messages.error(request, "There was an error in your form. Please correct the issues below") 
    else: 
        form = UserCreationForm() 
    return render(request, 'register.html', {'form': form})

class UserLoginView(LoginView): 
    template_name = 'login.html'
    redirect_authenticated_user = True 
    success_url = reverse_lazy('home') 
    

class UserLogoutView(LogoutView): 
    next_page = 'login'  
    
    