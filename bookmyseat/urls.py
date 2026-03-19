from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from users import views

urlpatterns = [
    path('favicon.ico', views.favicon, name='favicon'),
    path('favicon.png', views.favicon, name='favicon_png'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('users.urls')),
    path('movies/', include('movies.urls')),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),

]

if settings.DEBUG or getattr(settings, "USE_SQLITE_LOCAL", False):
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
