import logging
from types import SimpleNamespace
from urllib.parse import quote_plus
from pathlib import Path

from django.conf import settings
from django.db.utils import DatabaseError, OperationalError

from .models import Movie, Theater


logger = logging.getLogger(__name__)
DATABASE_ERRORS = (OperationalError, DatabaseError)


def _can_use_sqlite_fallback():
    return getattr(settings, "DEMO_MODE", False) or getattr(settings, "ALLOW_SQLITE_FALLBACK", False)


def _apply_movie_filters(queryset, search_query=None, genre=None, language=None):
    if search_query:
        queryset = queryset.filter(name__icontains=search_query)

    if genre:
        queryset = queryset.filter(genre__iexact=genre.strip())

    if language:
        queryset = queryset.filter(language__iexact=language.strip())

    return queryset


def _build_poster_url(movie):
    image = getattr(movie, "image", None)
    image_name = str(image or "").strip()
    image_public_id = getattr(image, "public_id", image_name).strip()

    if getattr(settings, "USE_SQLITE_LOCAL", False) and image_public_id:
        media_root = Path(settings.MEDIA_ROOT)
        exact_candidates = [
            media_root / image_name.replace("/", str(Path("/"))),
            media_root / image_public_id.replace("/", str(Path("/"))),
        ]
        for candidate in exact_candidates:
            if candidate.exists() and candidate.is_file():
                relative_path = candidate.relative_to(media_root).as_posix()
                return f"{settings.MEDIA_URL}{relative_path}"

        for candidate in media_root.glob(f"{image_public_id}.*"):
            if candidate.is_file():
                relative_path = candidate.relative_to(media_root).as_posix()
                return f"{settings.MEDIA_URL}{relative_path}"

    if image:
        try:
            return image.url
        except Exception:
            pass

    if image_name and (getattr(settings, "DEBUG", False) or getattr(settings, "USE_SQLITE_LOCAL", False)):
        return f"{settings.MEDIA_URL}{image_name.lstrip('/')}"

    return (
        "https://placehold.co/600x900/111827/f8fafc"
        f"?text={quote_plus(getattr(movie, 'name', 'BookMySeat'))}"
    )


def _serialize_movie(movie):
    return SimpleNamespace(
        id=movie.id,
        name=movie.name,
        image=SimpleNamespace(url=_build_poster_url(movie)),
        rating=getattr(movie, "rating", ""),
        genre=getattr(movie, "genre", ""),
        language=getattr(movie, "language", ""),
        description=getattr(movie, "description", ""),
        trailer_url=getattr(movie, "trailer_url", None),
        cast=getattr(movie, "cast", ""),
    )


def _serialize_theater(theater):
    show_time = getattr(theater, "time", None)
    if hasattr(show_time, "strftime"):
        show_time = show_time.strftime("%d %b %Y, %I:%M %p")

    return SimpleNamespace(
        id=theater.id,
        name=theater.name,
        time=show_time or "Time Not Set",
    )


def get_catalog_movies(search_query=None, genre=None, language=None):
    try:
        queryset = _apply_movie_filters(
            Movie.objects.all(),
            search_query=search_query,
            genre=genre,
            language=language,
        )
        return [_serialize_movie(movie) for movie in queryset], False
    except DATABASE_ERRORS:
        logger.warning(
            "Primary database is unavailable. Serving movie catalog from sqlite fallback.",
            exc_info=True,
        )
        if not _can_use_sqlite_fallback():
            raise

    try:
        queryset = _apply_movie_filters(
            Movie.objects.using("sqlite_fallback").all(),
            search_query=search_query,
            genre=genre,
            language=language,
        )
        return [_serialize_movie(movie) for movie in queryset], True
    except DATABASE_ERRORS:
        logger.warning(
            "SQLite fallback catalog is also unavailable. Returning an empty movie list.",
            exc_info=True,
        )
        return [], True


def get_movie_with_theaters(movie_id):
    try:
        movie = Movie.objects.filter(id=movie_id).first()
        if movie is None:
            return None, [], False

        theaters = Theater.objects.filter(movie_id=movie_id).order_by("time")
        return _serialize_movie(movie), [_serialize_theater(theater) for theater in theaters], False
    except DATABASE_ERRORS:
        logger.warning(
            "Primary database is unavailable. Serving theater list from sqlite fallback.",
            exc_info=True,
        )
        if not _can_use_sqlite_fallback():
            raise

    try:
        movie = Movie.objects.using("sqlite_fallback").filter(id=movie_id).first()
        if movie is None:
            return None, [], True

        theaters = Theater.objects.using("sqlite_fallback").filter(movie_id=movie_id).order_by("time")
        return _serialize_movie(movie), [_serialize_theater(theater) for theater in theaters], True
    except DATABASE_ERRORS:
        logger.warning(
            "SQLite fallback theater list is also unavailable.",
            exc_info=True,
        )
        return None, [], True
