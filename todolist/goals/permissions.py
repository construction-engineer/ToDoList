from typing import Any

from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, BasePermission
from rest_framework.request import Request

from todolist.goals.models import BoardParticipant, Board, GoalCategory, Goal, Comment


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id


class BoardPermissions(IsAuthenticated):
    def has_object_permission(self, request: Request, view, obj: Board) -> bool:
        _filters: dict[str: Any] = {'user_id': request.user.id, 'board_id': obj.id}
        if request.method not in SAFE_METHODS:
            _filters['role'] = BoardParticipant.Role.owner

        return BoardParticipant.objects.filter(**_filters).exists()


class GoalCategoryPermissions(IsAuthenticated):
    def has_object_permission(self, request: Request, view, goal_category: GoalCategory) -> bool:
        _filters: dict[str: Any] = {'user_id': request.user.id, 'board_id': goal_category.board_id}
        if request.method not in SAFE_METHODS:
            _filters['role__in'] = [BoardParticipant.Role.owner, BoardParticipant.Role.writer]
        return BoardParticipant.objects.filter(**_filters).exists()


class GoalPermissions(IsAuthenticated):
    def has_object_permission(self, request: Request, view, goal: Goal) -> bool:
        _filters: dict[str: Any] = {'user_id': request.user.id, 'board_id': goal.category.board_id}
        if request.method not in SAFE_METHODS:
            _filters['role__in'] = [BoardParticipant.Role.owner, BoardParticipant.Role.writer]
        return BoardParticipant.objects.filter(**_filters).exists()


class CommentPermissions(IsAuthenticated):
    def has_object_permission(self, request, view, obj: Comment):
        return any((
            request.method in SAFE_METHODS,
            obj.user.id == request.user.id
        ))
