from django.db import models
from django.utils import timezone
import math


class VehicleType(models.Model):
    name  = models.CharField(max_length=100, unique=True, verbose_name="Tur nomi")
    price = models.PositiveIntegerField(verbose_name="Narx (so'm/soat)")

    class Meta:
        verbose_name = "Transport turi"
        verbose_name_plural = "Transport turlari"

    def __str__(self):
        return f"{self.name} — {self.price:,} so'm/soat"


class Vehicle(models.Model):
    plate        = models.CharField(max_length=20, unique=True, verbose_name="Davlat raqami")
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, verbose_name="Turi")
    enter_time   = models.DateTimeField(default=timezone.now, verbose_name="Kirish vaqti")

    class Meta:
        verbose_name = "Ichkaridagi avtomobil"
        verbose_name_plural = "Ichkaridagi avtomobillar"

    def __str__(self):
        return self.plate

    def hours_parked(self):
        delta = timezone.now() - self.enter_time
        secs  = delta.total_seconds()
        return max(1, math.ceil(secs / 3600))

    def current_fee(self):
        return self.hours_parked() * self.vehicle_type.price


class ParkingHistory(models.Model):
    plate        = models.CharField(max_length=20, verbose_name="Davlat raqami")
    vehicle_type = models.CharField(max_length=100, verbose_name="Turi")
    enter_time   = models.DateTimeField(verbose_name="Kirish vaqti")
    exit_time    = models.DateTimeField(verbose_name="Chiqish vaqti")
    hours        = models.PositiveIntegerField(verbose_name="Soat")
    price        = models.PositiveIntegerField(verbose_name="To'lov (so'm)")
    date         = models.DateField(verbose_name="Sana")

    class Meta:
        verbose_name = "Tarix"
        verbose_name_plural = "Tarix"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.plate} — {self.price:,} so'm"


class SuperuserSecurityQuestion(models.Model):
    """Superuser parolini tiklash uchun maxfiy savol va hashed javob."""
    question        = models.CharField(max_length=300, verbose_name="Maxfiy savol")
    answer_hash     = models.CharField(max_length=256, verbose_name="Javob (hash)")
    created_at      = models.DateTimeField(auto_now_add=True)
    last_reset_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Maxfiy savol"
        verbose_name_plural = "Maxfiy savollar"

    def __str__(self):
        return self.question

    @classmethod
    def get_instance(cls):
        return cls.objects.first()


class Settings(models.Model):
    key   = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Sozlama"
        verbose_name_plural = "Sozlamalar"

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key, value):
        obj, _ = cls.objects.get_or_create(key=key)
        obj.value = str(value)
        obj.save()

    @classmethod
    def get_int(cls, key, default=0):
        try:
            return int(cls.get(key, default))
        except (TypeError, ValueError):
            return default
