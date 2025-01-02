"""
URL configuration for EMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from User_app import views
from User_app.views import CombinedLoginView, HomeView, SignupView, SigninView, search_events, SignoutView, DashboardLoginView, DashboardHomeView, CreateEventView, EventFormManagerView, ManageEventView, UpdateEventView, DeleteEventView, DashboardLogoutView, EventListView, EventFormFieldListView, EventRegistrationListView


urlpatterns = [
    path('admin/', admin.site.urls),

        ### EventPro Participant Website ###
    path('', CombinedLoginView.as_view(), name='login'),
    path('home/', HomeView.as_view(), name='home'),  
    path('signup/', SignupView.as_view(), name='signup'),
    path('signin/', SigninView.as_view(), name='signin'),
    path('search/', search_events, name='search_events'),
    path('event/<int:event_id>/register/', views.RegisterInEvent, name='register_event'),
    path('event/registration/<int:registration_id>/confirmation/', views.registration_confirmation, name='registration_confirmation'),
    path('User/', views.EventPro_User, name='user_account'),
    path('registration/<int:registration_id>/cancel/', views.cancel_registration, name='cancel_registration'),
    path('signout/', SignoutView.as_view(), name='signout'),

        ### EventPro Dashboard ###
    path('Dashboard_Login/', DashboardLoginView.as_view(), name='Dashboard_Login'),
    path('Dashboard_Home/', DashboardHomeView.as_view(), name='Dashboard_Home'),
    path('Create_Event/', CreateEventView.as_view(), name='Create_Event'),
    path('event/<int:event_id>/form-manager/', EventFormManagerView.as_view(), name='form_manager'),
    path('Manage_Event/', ManageEventView.as_view(), name='Manage_Event'),
    path('Update_Event/<int:pk>/', UpdateEventView.as_view(), name='Update_Event'),
    path('Delete_Event/<int:pk>/', DeleteEventView.as_view(), name='Delete_Event'),
    path('Dashboard_Logout/', DashboardLogoutView.as_view(), name='Dashboard_Logout'),

        ### EventPro Databases ###
    path('database/EventsTable/', EventListView.as_view(), name='event_database'),
    path('database/Form-FieldsTable/', EventFormFieldListView.as_view(), name='form_field_database'),
    path('database/RegistrationsTable/', EventRegistrationListView.as_view(), name='registration_database'),
]