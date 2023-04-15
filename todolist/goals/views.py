from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter

from todolist.goals.filters import GoalDateFilter
from todolist.goals.models import GoalCategory, Goal, Comment, BoardParticipant, Board
from todolist.goals.permissions import BoardPermissions, GoalCategoryPermissions, GoalPermissions, CommentPermissions, \
    IsOwnerOrReadOnly
from todolist.goals.serializers import GoalCategoryCreateSerializer, GoalCategorySerializer, GoalCreateSerializer, \
    GoalSerializer, CommentCreateSerializer, CommentSerializer, BoardCreateSerializer, BoardSerializer, \
    BoardListSerializer


class BoardCreateView(generics.CreateAPIView):
    serializer_class = BoardCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Делаем текущего пользователя владельцем доски"""
        BoardParticipant.objects.create(user=self.request.user, board=serializer.save())


class BoardListView(generics.ListAPIView):
    serializer_class = BoardListSerializer
    permission_classes = [BoardPermissions]
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title']

    def get_queryset(self):
        return Board.objects.prefetch_related('participants').filter(
            participants__user_id=self.request.user.id,
            is_deleted=False
        )


class BoardView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [BoardPermissions]
    serializer_class = BoardSerializer

    def get_queryset(self):
        return Board.objects.prefetch_related('participants').filter(
            participants__user_id=self.request.user.id,
            is_deleted=False
        )

    def perform_destroy(self, instance: Board):
        """
        При удалении доски помечаем ее как is_deleted,
        «удаляем» категории, обновляем статус целей
        """
        with transaction.atomic():
            instance.is_deleted = True
            instance.save()
            instance.categories.update(is_deleted=True)
            Goal.objects.filter(category__board=instance).update(
                status=Goal.Status.archived
            )
        return instance


class GoalCategoryCreateView(generics.CreateAPIView):
    permission_classes = [GoalCategoryPermissions]
    serializer_class = GoalCategoryCreateSerializer


class GoalCategoryListView(generics.ListAPIView):
    permission_classes = [GoalCategoryPermissions]
    serializer_class = GoalCategorySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['board']
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title']

    def get_queryset(self):
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            # board_id=self.request.query_params.get('board'),
            board__participants__user_id=self.request.user.id,
            is_deleted=False,
        )


class GoalCategoryView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GoalCategorySerializer
    permission_classes = [GoalCategoryPermissions, IsOwnerOrReadOnly]

    def get_queryset(self):
        return GoalCategory.objects.prefetch_related('board__participants').filter(
            board__participants__user_id=self.request.user.id,
            is_deleted=False
        )

    def perform_destroy(self, instance: GoalCategory) -> None:
        with transaction.atomic():
            instance.is_deleted = True
            instance.save(update_fields=('is_deleted',))
            instance.goals.update(status=Goal.Status.archived)


class GoalCreateView(generics.CreateAPIView):
    serializer_class = GoalCreateSerializer
    permission_classes = [GoalPermissions]


class GoalListView(generics.ListAPIView):
    serializer_class = GoalSerializer
    permission_classes = [GoalPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = GoalDateFilter
    ordering_fields = ['title', 'created']
    ordering = ['title']
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Goal.objects.filter(
            category__board__participants__user_id=self.request.user.id,
            category__is_deleted=False
        ).exclude(status=Goal.Status.archived)


class GoalView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [GoalPermissions, IsOwnerOrReadOnly]
    serializer_class = GoalSerializer

    def get_queryset(self):
        return Goal.objects.filter(
            category__is_deleted=False
        ).exclude(status=Goal.Status.archived)

    def perform_destroy(self, instance: Goal) -> None:
        instance.status = Goal.Status.archived
        instance.save(update_fields=('status',))


class CommentCreateView(generics.CreateAPIView):
    permission_classes = [CommentPermissions]
    serializer_class = CommentCreateSerializer


class CommentListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [CommentPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['goal']
    ordering_fields = ['updated', 'created']
    ordering = ['created']

    def get_queryset(self):
        return Comment.objects.filter(
            goal__category__board__participants__user_id=self.request.user.id
        )


class CommentView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [CommentPermissions, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(user_id=self.request.user.id)
