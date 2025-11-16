from django.db import models
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

# Create your models here.

class RoomCategory(models.Model):
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey(RoomCategory, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Room {self.room_number} ({self.category.name})"

    @classmethod
    def available_rooms(cls, category, start_date, end_date):
        booked_rooms = Reservation.objects.filter(
            room__category=category,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).values_list('room_id', flat=True)
        return cls.objects.filter(category=category).exclude(id__in=booked_rooms)

class SpecialRate(models.Model):
    room_category = models.ForeignKey(RoomCategory, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    rate_multiplier = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.room_category.name} special rate ({self.start_date} to {self.end_date})"

class Reservation(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    customer_name = models.CharField(max_length=200)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

    def clean(self):
        overlapping = Reservation.objects.filter(
            room=self.room,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(id=self.id)
        if overlapping.exists():
            raise ValidationError("This room is already booked for the selected dates.")

    def calculate_total_price(self):
        total = Decimal(0)
        current_date = self.start_date
        one_day = timedelta(days=1)

        while current_date < self.end_date:
            price = self.room.category.base_price
            special_rates = SpecialRate.objects.filter(
                room_category=self.room.category,
                start_date__lte=current_date,
                end_date__gte=current_date
            )

            if special_rates.exists():
                multiplier = max(sr.rate_multiplier for sr in special_rates)
                price *= multiplier
            total += price
            current_date += one_day
        return total.quantize(Decimal("0.01"))

    def save(self, *args, **kwargs):
        total = self.calculate_total_price()
        self.total_price = Decimal(total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - Room {self.room.room_number}"
