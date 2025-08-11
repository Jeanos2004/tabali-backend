# pages/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

def home_view(request):
    """Render the home page with login form."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue, {user.username} !')
            return redirect('pages:dashboard')
        else:
            messages.error(request, 'Identifiants invalides. Veuillez réessayer.')
            return redirect('pages:home')
    
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('pages:dashboard')
        
    return render(request, 'pages/home.html')

@login_required
def dashboard_view(request):
    """Dashboard view for authenticated users."""
    return render(request, 'pages/dashboard.html')

def logout_view(request):
    """Logout view."""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('pages:home')