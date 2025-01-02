from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView
from .forms import SignupForm, SigninForm, EventForm, DynamicEventRegistrationForm
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.views.generic import TemplateView, ListView
from django.urls import reverse_lazy
from .models import Event, EventFormField, EventRegistration
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime, timedelta


### EventPro Classes (Participant Side) ###
class SignupView(FormView):
    template_name = "Participant_Pages/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy('signin')

    def form_valid(self, form):
        username = form.cleaned_data['username']
        fname = form.cleaned_data['fname']
        lname = form.cleaned_data['lname']
        email = form.cleaned_data['email']
        pass1 = form.cleaned_data['pass1']

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(self.request, "Username already exists!")
            return self.form_invalid(form)

        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()

        messages.success(self.request, "Account Created Successfully, welcome!")
        return super().form_valid(form)

class SigninView(FormView):
    template_name = "Participant_Pages/signin.html"
    form_class = SigninForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        pass1 = form.cleaned_data['pass1']
        
        try:
            # Get the username associated with this email
            user = User.objects.get(email=email)
            # Authenticate with the username
            user = authenticate(username=user.username, password=pass1)
            
            if user is not None:
                login(self.request, user)
                messages.success(self.request, f"Welcome back, {user.first_name}!")
                return super().form_valid(form)
            else:
                messages.error(self.request, "Invalid email or password!")
                return self.form_invalid(form)
                
        except User.DoesNotExist:
            messages.error(self.request, "Invalid email or password!")
            return self.form_invalid(form)

class CombinedLoginView(View):
    template_name = "combined_login.html"
    def get(self, request):
        participant_form = SigninForm()
        return render(request, self.template_name, {
            'participant_form': participant_form
        })

    def post(self, request):
        login_type = request.POST.get('login_type')
        
        if login_type == 'manager':
            username = request.POST.get('username')
            password = request.POST.get('pass1')
            if username == "EventsAdmin1" and password == "admin1":
                request.session['admin_logged_in'] = True
                messages.success(request, "Logged in successfully!")
                return redirect('Dashboard_Home')
            messages.error(request, "Invalid manager credentials!")
            
        else:  # participant login
            form = SigninForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['pass1']
                try:
                    user = User.objects.get(email=email)
                    user = authenticate(username=user.username, password=password)
                    if user is not None:
                        login(request, user)
                        messages.success(request, f"Welcome back, {user.first_name}!")
                        return redirect('home')
                except User.DoesNotExist:
                    pass
                messages.error(request, "Invalid email or password!")
        return redirect('login')
    

class HomeView(ListView):
   model = Event 
   template_name = 'Participant_Pages/home.html'
   context_object_name = 'events'

   def get_queryset(self):
       return Event.objects.values('EventType').distinct().order_by('EventType')

   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       if self.request.user.is_authenticated:
           context['fname'] = self.request.user.first_name

       upcoming_events = Event.objects.filter(
           EventDate__gte=datetime.now().date()
       ).order_by('?')[:6]

       # Calculate capacity percentage for each event
       for event in upcoming_events:
           event.registration_deadline = datetime.combine(
               event.EventDate, 
               event.EventTime
           ) - timedelta(hours=24)
           
           # Calculate capacity percentage
           if event.EventCapacity:
               event.capacity_percentage = (event.current_participants / event.EventCapacity) * 100
           else:
               event.capacity_percentage = 0
           
       context['featured_events'] = upcoming_events
       context['current_time'] = datetime.now()
       return context

def search_events(request):
   event_type = request.GET.get('event_type')
   events = None
   
   try:
       if event_type:
           events = Event.objects.filter(EventType=event_type)
           if not events.exists():
               messages.info(request, f"No events found for type: {event_type}")
   except Exception as e:
       messages.error(request, "Search error. Please try again.")
       
   context = {
       'events': events,
       'searched_type': event_type,
       'fname': request.user.first_name if request.user.is_authenticated else None
   }
   
   return render(request, 'Participant_Pages/SearchResult.html', context)

@login_required
def RegisterInEvent(request, event_id):
    event = get_object_or_404(Event, EventID=event_id)
    
# Check if event registration form is configured
    if not event.form_configured:
        messages.error(request, "Registration is not yet available for this event.")
        return redirect('home')

    # Check if event is full
    if event.EventCapacity and event.current_participants >= event.EventCapacity:
        messages.error(request, "Sorry, this event is already full!")
        return redirect('home')
    
    # Check if user is already registered
    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.warning(request, "You are already registered for this event!")
        return redirect('home')
    
    if request.method == 'POST':
        form = DynamicEventRegistrationForm(event=event, user=request.user, data=request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Prepare payment status based on event cost
                    payment_status = 'not_required' if event.EventCost.lower() == 'free' else 'pending'
                    payment_method = form.cleaned_data.get('payment_method') if event.EventCost.lower() != 'free' else None
                    
                    # Get form data and ensure email matches user's email
                    registration_data = form.cleaned_data.copy()
                    for field_id, value in form.cleaned_data.items():
                        if field_id.startswith('field_'):
                            field = EventFormField.objects.get(id=field_id.split('_')[1])
                            if field.field_type == 'email':
                                registration_data[field_id] = request.user.email
                    
                    # Create registration record
                    registration = EventRegistration.objects.create(
                        event=event,
                        user=request.user,
                        registration_data=registration_data,
                        payment_status=payment_status,
                        payment_method=payment_method
                    )
                return redirect('registration_confirmation', registration_id=registration.id)
                
            except Exception as e:
                print(f"Registration error: {str(e)}")  # For debugging
                messages.error(request, "An error occurred during registration. Please try again.")
                return render(request, 'Participant_Pages/RegisterInEvent.html', {
                    'event': event,
                    'form': form,
                    'remaining_spots': event.EventCapacity - event.current_participants if event.EventCapacity else None
                })
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # For GET request, initialize form with user's email
        initial_data = {}
        for field in event.form_fields.all():
            if field.field_type == 'email':
                initial_data[f'field_{field.id}'] = request.user.email
        form = DynamicEventRegistrationForm(event=event, user=request.user, initial=initial_data)
    
    # Add capacity information to template context
    remaining_spots = event.EventCapacity - event.current_participants if event.EventCapacity else None
    
    return render(request, 'Participant_Pages/RegisterInEvent.html', {
        'event': event,
        'form': form,
        'remaining_spots': remaining_spots
    })

@login_required
def registration_confirmation(request, registration_id):
    registration = get_object_or_404(EventRegistration, id=registration_id, user=request.user)
    event = registration.event
    
    context = {
        'registration': registration,
        'event': event,
        'user': request.user,
        'date': datetime.now().strftime('%B %d, %Y')
    }
    return render(request, 'Participant_Pages/registration_confirmation.html', context)

@login_required
def EventPro_User(request):
    try:
        # Get user's registered events with all related data
        user_registrations = EventRegistration.objects.filter(
            user=request.user
        ).select_related('event').order_by('-created_at')
        
        context = {
            'user': request.user,
            'registrations': user_registrations,
            'has_registrations': user_registrations.exists(),
            'fname': request.user.first_name
        }
        return render(request, 'Participant_Pages/MyAccount.html', context)
    except Exception as e:
        print(f"Error in EventPro_User view: {str(e)}")
        messages.error(request, "An error occurred while loading your account.")
        return redirect('home')

@login_required
def cancel_registration(request, registration_id):
    try:
        registration = EventRegistration.objects.get(id=registration_id, user=request.user)
        event = registration.event
        registration.delete()
        event.remove_participant()
        messages.success(request, "Registration cancelled successfully!")
        return redirect('user_account')
    except EventRegistration.DoesNotExist:
        messages.error(request, "Registration not found!")
        return redirect('user_account')

class SignoutView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "Logged out successfully!")
        return redirect('home')
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "Logged out successfully!")
        return redirect('home')


    ### EventPro Dashboard Classes ###
class DashboardLoginView(View):
    def get(self, request):
        return render(request, "Dashboard_Pages/Dashboard_Login.html")

    def post(self, request):
        username = request.POST['username']
        pass1 = request.POST['pass1']
        admin_username = "EventsAdmin1"
        admin_password = "admin1"
        if username == admin_username and pass1 == admin_password:
            request.session['admin_logged_in'] = True
            messages.success(request, "Logged in successfully!")
            return redirect('Dashboard_Home')
        else:
            messages.error(request, "Username or password is incorrect!")
            return redirect('Dashboard_Login')

class DashboardHomeView(TemplateView):
    template_name = "Dashboard_Pages/Dashboard_Home.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all'] = Event.objects.all()
        return context

class CreateEventView(CreateView):
    model = Event
    form_class = EventForm
    template_name = "Dashboard_Pages/CreateEvent.html"
    success_url = reverse_lazy('Dashboard_Home')

    def form_valid(self, form):
        # First save the form to create the event object
        event = form.save(commit=False)
        
        # Handle capacity
        capacity_value = form.cleaned_data.get('EventCapacity')
        if capacity_value:
            event.EventCapacity = capacity_value
        else:
            event.EventCapacity = None
            
        # Set initial participants count
        event.current_participants = 0
        event.form_configured = False
        event.save()
        
        # Add basic/common fields automatically
        basic_fields = [
            ('Full Name', 'text'),
            ('Gender', 'select', 'Male,Female'),
            ('Email', 'email'),
            ('Phone Number', 'text')
        ]
        
        # Create the basic fields
        for field_info in basic_fields:
            field_name, field_type, *extra = field_info
            field_data = {
                'event': event,
                'field_name': field_name,
                'field_type': field_type,
                'is_required': True
            }

            if len(field_info) > 2:
                field_data['choices'] = field_info[2]
            EventFormField.objects.create(**field_data)
        # Add payment method field for paid events
        if event.EventCost.lower() != 'free':
            EventFormField.objects.create(
                event=event,
                field_name='Payment Method',
                field_type='select',
                is_required=True,
                choices='Credit Card,Debit Card,Cash'
            )
        messages.success(self.request, "Event has been created successfully!")
        return super().form_valid(form)

class EventFormManagerView(View):
    template_name = "Dashboard_Pages/form_manager.html"
    def get(self, request, event_id):
        event = get_object_or_404(Event, EventID=event_id)
        form_fields = event.form_fields.all()
        return render(request, self.template_name, {
            'event': event,
            'form_fields': form_fields
        })
    def post(self, request, event_id):
        event = get_object_or_404(Event, EventID=event_id)
        action = request.POST.get('action')
        if action == 'add_field':
            field_name = request.POST.get('field_name')
            field_type = request.POST.get('field_type')
            is_required = request.POST.get('is_required') == 'on'
            choices = request.POST.get('choices') if field_type == 'select' else None
            EventFormField.objects.create(
                event=event,
                field_name=field_name,
                field_type=field_type,
                is_required=is_required,
                choices=choices
            )
            messages.success(request, "Field added successfully!")
        elif action == 'delete_field':
            field_id = request.POST.get('field_id')
            EventFormField.objects.filter(id=field_id, event=event).delete()
            messages.success(request, "Field removed successfully!")
        elif action == 'save_form':
            event.form_configured = True
            event.save()
            messages.success(request, "Form configuration saved!")
            return redirect('Dashboard_Home')
        return redirect('form_manager', event_id=event_id)

class ManageEventView(ListView):
        model = Event
        template_name = "Dashboard_Pages/ManageEvent.html"
        context_object_name = 'all'

class UpdateEventView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = "Dashboard_Pages/UpdateEvent.html"
    success_url = reverse_lazy('Dashboard_Home')
    def form_valid(self, form):
        messages.success(self.request, "Event updated successfully!")
        return super().form_valid(form)

class DeleteEventView(View):
    def post(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs['pk'])
        event.delete()
        messages.success(request, "Event deleted successfully!")
        return redirect('Dashboard_Home')

class DashboardLogoutView(View):
    def get(self, request):
        logout(request)
        messages.success(request, "Logged out successfully!")
        return redirect('Dashboard_Login')
    

    ### EventPro Database Pages ###
class EventListView(ListView):
    model = Event
    template_name = 'Database_Pages/event_database.html'
    context_object_name = 'events'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Events Database'
        return context

class EventFormFieldListView(ListView):
    model = EventFormField
    template_name = 'Database_Pages/form_field_database.html'
    context_object_name = 'form_fields'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Event Form Fields Database'
        return context

class EventRegistrationListView(ListView):
    model = EventRegistration
    template_name = 'Database_Pages/registration_database.html'
    context_object_name = 'registrations'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Event Registrations Database'
        return context