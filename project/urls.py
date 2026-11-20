"""URL configuration for project project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path

from users.views import demo_login, home, login, logout, registration
from workers.views import (book_worker, cancel_booking, complete_job,
                           edit_profile, leave_review, my_bookings, start_job,
                           toggle_available_now, update_booking, view_bookings,
                           worker_detail, worker_login, worker_register,
                           workers_list)

urlpatterns = [
    path('', lambda request: redirect('/home/')),
    path('admin/', admin.site.urls),
    path('home/', home, name='home'),
    path('registration/', registration, name='registration'),
    path('worker_register/', worker_register, name='worker_register'),
    path('workers/', workers_list, name='workers'),
    path('worker/<int:pk>/', worker_detail, name='worker_detail'),
    path('book/<int:pk>/', book_worker, name='book'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('worker_login/', worker_login, name='worker_login'),
    path('view_bookings/', view_bookings, name='view_bookings'),
    path('edit_profile/', edit_profile, name='edit_profile'),
    path('update_booking/<int:pk>/', update_booking, name='update_booking'),
    path('start_job/<int:pk>/', start_job, name='start_job'),
    path('complete_job/<int:pk>/', complete_job, name='complete_job'),
    path('toggle_available_now/', toggle_available_now, name='toggle_available_now'),
    path('my_bookings/', my_bookings, name='my_bookings'),
    path('cancel_booking/<int:pk>/', cancel_booking, name='cancel_booking'),
    path('leave_review/<int:pk>/', leave_review, name='leave_review'),
    path('demo_login/<str:role>/', demo_login, name='demo_login'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
