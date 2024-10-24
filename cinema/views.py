from django.db.models import Count, F
from rest_framework import viewsets

from cinema.models import Genre, Actor, CinemaHall, Movie, MovieSession, Order
from cinema.paginations import OrderPagination

from cinema.serializers import (
    GenreSerializer,
    ActorSerializer,
    CinemaHallSerializer,
    MovieSerializer,
    MovieSessionSerializer,
    MovieSessionListSerializer,
    MovieDetailSerializer,
    MovieSessionDetailSerializer,
    MovieListSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class ActorViewSet(viewsets.ModelViewSet):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer


class CinemaHallViewSet(viewsets.ModelViewSet):
    queryset = CinemaHall.objects.all()
    serializer_class = CinemaHallSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return MovieListSerializer

        if self.action == "retrieve":
            return MovieDetailSerializer

        return MovieSerializer

    def get_queryset(self):
        queryset = self.queryset.prefetch_related("genres", "actors")

        if self.action == "list":
            genres = self.request.query_params.get("genres")
            actors = self.request.query_params.get("actors")
            title = self.request.query_params.get("title")

            if genres:
                genres_ids = [int(str_id) for str_id in genres.split(",")]
                queryset = queryset.filter(genres__id__in=genres_ids)
            if actors:
                actors_ids = [int(str_id) for str_id in actors.split(",")]
                queryset = queryset.filter(actors__id__in=actors_ids)
            if title:
                queryset = queryset.filter(title__icontains=title)

        return queryset


class MovieSessionViewSet(viewsets.ModelViewSet):
    queryset = MovieSession.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return MovieSessionListSerializer

        if self.action == "retrieve":
            return MovieSessionDetailSerializer

        return MovieSessionSerializer

    def get_queryset(self):
        queryset = self.queryset.select_related("movie", "cinema_hall")

        if self.action == "list":
            queryset = queryset.prefetch_related("tickets").annotate(
                tickets_available=(
                    F("cinema_hall__rows") * F("cinema_hall__seats_in_row")
                    - Count("tickets")
                )
            )

            movie_id = self.request.query_params.get("movie")
            date = self.request.query_params.get("date")

            if movie_id:
                queryset = queryset.filter(movie=movie_id)
            if date:
                queryset = queryset.filter(show_time__date=date)

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).prefetch_related(
            "tickets__movie_session__cinema_hall",
            "tickets__movie_session__movie"
        )

    def get_serializer_class(self):
        return (
            OrderListSerializer if self.action == "list"
            else OrderSerializer
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
