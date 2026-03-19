from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import Http404, HttpResponse

from .catalog import get_catalog_movies, get_movie_with_theaters
from .models import Movie, Theater, Seat, Booking

import razorpay
import hmac, hashlib
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from django.contrib.admin.views.decorators import staff_member_required



# =========================
# HELPER: CLEAR EXPIRED RESERVATIONS
# =========================
def clear_expired_reservations():
    Seat.objects.filter(
        is_booked=False,
        reserved_until__lt=timezone.now()
    ).update(reserved_until=None)


# =========================
# MOVIE LIST
# =========================
def movie_list(request):
    search_query = request.GET.get('search')
    genre = request.GET.get('genre')
    language = request.GET.get('language')

    movies, using_demo_data = get_catalog_movies(
        search_query=search_query,
        genre=genre,
        language=language,
    )

    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'using_demo_data': using_demo_data,
    })


# =========================
# THEATER LIST
# =========================
def theater_list(request, movie_id):
    movie, theaters, using_demo_data = get_movie_with_theaters(movie_id)
    if movie is None:
        raise Http404("Movie not found")

    return render(request, 'movies/theater_list.html', {
        'movie': movie,
        'theaters': theaters,
        'booking_available': not using_demo_data,
        'using_demo_data': using_demo_data,
    })


# =========================
# SEAT SELECTION + RESERVE
# =========================
@login_required(login_url='/login/')
def book_seats(request, theater_id):

    clear_expired_reservations()

    theater = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theater)

    if request.method == "POST":

        seat_id = request.POST.get("seat_id")

        if not seat_id:
            return HttpResponse("No seat selected")

        seat = get_object_or_404(Seat, id=seat_id, theater=theater)

        # block if booked or reserved
        if seat.is_booked or (seat.reserved_until and seat.reserved_until > timezone.now()):
            return HttpResponse("Seat already reserved or booked")

        # reserve seat for 5 minutes
        seat.reserved_until = timezone.now() + timedelta(minutes=5)
        seat.save()

        booking = Booking.objects.create(
            user=request.user,
            movie=theater.movie,
            theater=theater,
            seat=seat,
            total_price=200
        )

        return redirect("payment_page", booking_id=booking.id)

    return render(request, "movies/seat_selection.html", {
        "theater": theater,
        "seats": seats,
        "now": timezone.now()
    })


# =========================
# PAYMENT PAGE
# =========================
def payment_page(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id)

    client = razorpay.Client(auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    ))

    order = client.order.create({
        "amount": booking.total_price * 100,
        "currency": "INR",
        "payment_capture": "1"
    })

    booking.razorpay_order_id = order["id"]
    booking.save()

    return render(request, "movies/payment.html", {
        "booking": booking,
        "order": order,
        "razorpay_key": settings.RAZORPAY_KEY_ID
    })


# =========================
# PAYMENT SUCCESS
# =========================
def payment_success(request):

    razorpay_payment_id = request.GET.get("razorpay_payment_id")
    razorpay_order_id = request.GET.get("razorpay_order_id")
    razorpay_signature = request.GET.get("razorpay_signature")
    booking_id = request.GET.get("booking_id")

    booking = get_object_or_404(Booking, id=booking_id)
    seat = booking.seat

    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()

    # verification failed
    if generated_signature != razorpay_signature:
        if seat:
            seat.reserved_until = None
            seat.save()

        booking.delete()
        return HttpResponse("Payment verification failed")

    # mark booking paid
    booking.payment_id = razorpay_payment_id
    booking.razorpay_order_id = razorpay_order_id
    booking.is_paid = True
    booking.save()

    if not seat:
        return HttpResponse("No seat attached to this booking")

    if seat.is_booked:
        return HttpResponse("Seat already booked")

    # finalize seat booking
    seat.is_booked = True
    seat.reserved_until = None
    seat.save()

    send_mail(
        subject="Your Ticket Booking is Confirmed 🎟️",
        message=f"""
Hi {booking.user.username},

Your ticket booking is confirmed! 🎉

Movie: {booking.movie.name}
Theater: {booking.theater.name}
Seat: {seat.seat_number}

Thank you for booking with us 😊
""",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[booking.user.email],
        fail_silently=False,
    )

    return render(request, "movies/payment_success.html", {
        "booking": booking,
        "seat": seat
    })


# =========================
# PAYMENT FAILED
# =========================
def payment_failed(request):
    return render(request, "movies/payment_failed.html")


@staff_member_required
def admin_dashboard(request):

    # Only paid bookings
    bookings = Booking.objects.filter(is_paid=True)

    total_revenue = bookings.aggregate(total=Sum("total_price"))["total"] or 0
    total_bookings = bookings.count()

    popular_movies = (
        bookings.values("movie__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    busiest_theaters = (
        bookings.values("theater__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    return render(request, "movies/admin_dashboard.html", {
        "total_revenue": total_revenue,
        "total_bookings": total_bookings,
        "popular_movies": popular_movies,
        "busiest_theaters": busiest_theaters,
    })
