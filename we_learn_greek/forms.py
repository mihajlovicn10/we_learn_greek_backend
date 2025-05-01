from django.contrib import admin 
from django import forms 
from django.contrib.auth.forms import UserCreationForm , UserChangeForm
from django.contrib.auth.admin import UserAdmin 
from .models import User 

class CustomUserCreationForm(UserCreationForm): 
    class Meta: 
        model = User 
        fields = ('email' , 'first_name' , 'last_name' , 'last_name' , 'password1' , 'password2')
        
class CustomUserChangeForm(UserChangeForm): 
    class Meta: 
        model = User
        fields = ['email' , 'first_name' , 'last_name'] 
        
class CustomUserAdmin(UserAdmin): 
    add_form = CustomUserCreationForm 
    form = CustomUserChangeForm 
    model = User 
    list_display = ['email', 'first_name', 'last_name', 'is_staff'] 
    fieldsets = (
        (None, {'fields': ('email', 'password', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )        
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'is_active')}
        ),
    )
    ordering = ['email']
    
admin.site.register(User, CustomUserAdmin) 