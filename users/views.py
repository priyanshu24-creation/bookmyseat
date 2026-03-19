from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .forms import UserRegisterForm, UserUpdateForm
from django.shortcuts import render,redirect
from django.conf import settings
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from movies.catalog import get_catalog_movies
from movies.models import Booking

def home(request):
    movies, using_demo_data = get_catalog_movies(
        genre=request.GET.get('genre'),
        language=request.GET.get('language'),
    )
    return render(request, 'users/home.html', {
        'movies': movies,
        'using_demo_data': using_demo_data,
    })


def favicon(request):
    favicon_path = settings.BASE_DIR / "static" / "favicon.svg"
    if not favicon_path.exists():
        raise Http404("Favicon not found")
    return FileResponse(favicon_path.open("rb"), content_type="image/svg+xml")


def register(request):
    if request.method == 'POST':
        form=UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data.get('username')
            password=form.cleaned_data.get('password1')
            user=authenticate(username=username,password=password)
            login(request,user)
            return redirect('profile')
    else:
        form=UserRegisterForm()
    return render(request,'users/register.html',{'form':form})

def login_view(request):
    if request.method == 'POST':
        form=AuthenticationForm(request,data=request.POST)
        if form.is_valid():
            user=form.get_user()
            login(request,user)
            return redirect('/')
    else:
        form=AuthenticationForm()
    return render(request,'users/login.html',{'form':form})

@login_required
def profile(request):
    bookings= Booking.objects.filter(user=request.user)
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)

    return render(request, 'users/profile.html', {'u_form': u_form,'bookings':bookings})

@login_required
def reset_password(request):
    if request.method == 'POST':
        form=PasswordChangeForm(user=request.user,data=request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form=PasswordChangeForm(user=request.user)
    return render(request,'users/reset_password.html',{'form':form})
def admin_dashboard(request):
    return render(request, "movies/admin_dashboard.html")
