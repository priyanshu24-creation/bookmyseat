from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField


class Movie(models.Model):
    GENRE_CHOICES = [
        ('action','Action'),
        ('comedy','Comedy'),
        ('drama','Drama'),
        ('thriller','Thriller'),
        ('horror','Horror'),
        ('romance','Romance'),
        ('biography','Biography'),
        ('animation','Animation'),


    ]

    LANGUAGE_CHOICES = [
        ('hindi','Hindi'),
        ('english','English'),
        ('tamil','Tamil'),
        ('telugu','Telugu'),
    ]

    name = models.CharField(max_length=200)
    image = CloudinaryField('image')
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    description = models.TextField()
    trailer_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

class Theater(models.Model):
    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie,on_delete=models.CASCADE,related_name='theaters')
    time= models.DateTimeField()

    def __str__(self):
        return f'{self.name} - {self.movie.name} at {self.time}'

class Seat(models.Model):
    theater = models.ForeignKey(Theater,on_delete=models.CASCADE,related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)

    reserved_until = models.DateTimeField(null=True, blank=True)

    def is_reserved(self):
        if self.reserved_until:
            return self.reserved_until > timezone.now()
        return False

    def __str__(self):
        return f'{self.seat_number} in {self.theater.name}'
    
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, null=True, blank=True)

    total_price = models.IntegerField(default=0)

    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)

    is_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.movie.name}"
