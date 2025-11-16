from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from .forms import RegisterForm
from .models import Room, Reservation, RoomCategory, SpecialRate
from .forms import AvailabilityForm, SpecialRateForm, RoomForm, RoomCategoryForm
from datetime import datetime

def home(request):
    return render(request, 'index.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('home')

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    rooms = Room.objects.all()
    reservations = Reservation.objects.all()
    return render(request, 'admin_dashboard.html', {
        'rooms': rooms,
        'reservations': reservations
    })
def check_availability(category, start_date, end_date):
    rooms = Room.objects.filter(category=category)
    unavailable_rooms = Reservation.objects.filter(
        room__in=rooms,
        start_date__lt=end_date,
        end_date__gt=start_date
    ).values_list('room_id', flat=True)
    available_rooms = rooms.exclude(id__in=unavailable_rooms)
    return available_rooms

@login_required
def user_dashboard(request):
    form = AvailabilityForm(request.POST or None)
    available_rooms = None
    reservations = Reservation.objects.filter(customer_name=request.user.username)
    start_date = end_date = category = None

    if request.method == 'POST' and form.is_valid():
        category = form.cleaned_data['category']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        available_rooms = check_availability(category, start_date, end_date)
    return render(request, 'user_dashboard.html', {
        'form': form,
        'available_rooms': available_rooms,
        'start_date': start_date,
        'end_date': end_date,
        'category': category,
        'reservations': reservations
    })

@login_required
def confirm_booking(request, room_id, start, end):
    room = get_object_or_404(Room, id=room_id)
    start_date = datetime.fromisoformat(start).date()
    end_date = datetime.fromisoformat(end).date()
    overlap = Reservation.objects.filter(
        room=room,
        start_date__lt=end_date,
        end_date__gt=start_date
    ).exists()

    if overlap:
        messages.error(request, "This room is no longer available for those dates.")
        return redirect('user_dashboard')

    days = (end_date - start_date).days or 1
    temp_reservation = Reservation(
        room=room,
        start_date=start_date,
        end_date=end_date
    )
    total_price = temp_reservation.calculate_total_price()

    if request.method == 'POST':
        Reservation.objects.create(
            room=room,
            start_date=start_date,
            end_date=end_date,
            customer_name=request.user.username,
            total_price=total_price
        )
        messages.success(request, "Booking confirmed successfully!")
        return redirect('booking_success')

    return render(request, 'confirm_booking.html', {
        'room': room,
        'start_date': start_date,
        'end_date': end_date,
        'total_price': total_price
    })

@login_required
def booking_success(request):
    return render(request, 'booking_success.html')

def manage_categories(request):
    categories = RoomCategory.objects.all()
    form = RoomCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Room Category added successfully.")
        return redirect('manage_categories')
    return render(request, 'manage_categories.html', {'form': form, 'categories': categories})

@login_required
def manage_rooms(request):
    rooms = Room.objects.all().select_related('category')
    form = RoomForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Room added successfully.")
        return redirect('manage_rooms')
    return render(request, 'manage_rooms.html', {'rooms': rooms, 'form': form})

@login_required
def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    form = RoomForm(request.POST or None, instance=room)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Room {room.room_number} updated successfully.")
        return redirect('manage_rooms')

    return render(request, 'edit_room.html', {'form': form, 'room': room})


@login_required
def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    messages.success(request, f"Room {room.room_number} deleted successfully.")
    return redirect('manage_rooms')

def manage_rates(request):
    rates = SpecialRate.objects.select_related('room_category').all()
    form = SpecialRateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Special Rate added successfully.")
        return redirect('manage_rates')
    return render(request, 'manage_rates.html', {'form': form, 'rates': rates})