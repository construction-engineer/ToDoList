from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from todolist.core.models import User
from todolist.core.serializers import ProfileSerializer
from todolist.goals.models import GoalCategory, Goal, Comment, Board, BoardParticipant


class BoardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'is_deleted')


class BoardParticipantSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(required=True, choices=BoardParticipant.Role.choices[1:])
    user = serializers.SlugRelatedField(slug_field="username", queryset=User.objects.all())

    class Meta:
        model = BoardParticipant
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'board')


class BoardSerializer(serializers.ModelSerializer):
    participants = BoardParticipantSerializer(many=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        fields = "__all__"
        read_only_fields = ('id', 'created', 'updated', 'is_deleted')

    def update(self, instance: Board, validated_data: dict) -> Board:
        request: Request = self.context['request']

        with transaction.atomic():
            BoardParticipant.objects.filter(board=instance).exclude(user=request.user).delete()
            BoardParticipant.objects.bulk_create(
                [
                    BoardParticipant(user=participant['user'], role=participant['role'], board=instance) for participant
                    in validated_data.get('participants', [])
                ],
                ignore_conflicts=True
            )

            if title := validated_data.get('title'):
                instance.title = title
            instance.save()

        return instance


class BoardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = "__all__"


class GoalCategoryCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    def validate_board(self, board: Board) -> Board:
        if board.is_deleted:
            raise serializers.ValidationError('Board is deleted')

        if not BoardParticipant.objects.filter(
                board_id=board.id,
                user_id=self.context['request'].user.id,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer]
        ).exists():
            raise PermissionDenied
        return board

    class Meta:
        model = GoalCategory
        read_only_fields = ('id', 'created', 'updated', 'user', 'is_deleted')
        fields = '__all__'


class GoalCategorySerializer(serializers.ModelSerializer):
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = GoalCategory
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user', 'board', 'is_deleted')


class GoalCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validate_category(self, category: GoalCategory):
        if category.is_deleted:
            raise serializers.ValidationError('not allowed in deleted category')
        if not BoardParticipant.objects.filter(
                board_id=category.board_id,
                user_id=self.context['request'].user.id,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
        ).exists():
            raise PermissionDenied
        return category


class GoalSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = Goal
        read_only_fields = ('id', 'created', 'updated', 'user')
        fields = '__all__'

    def validate_category(self, value: GoalCategory):
        if value.is_deleted:
            raise serializers.ValidationError('not allowed in deleted category')
        if self.context['request'].user.id != value.user_id:
            raise PermissionDenied
        return value


class CommentCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ('id', 'created', 'updated', 'user')

    def validate_goal(self, goal: Goal) -> Goal:
        if not BoardParticipant.objects.filter(
                board_id=goal.category.board_id,
                user_id=self.context['request'].user.id,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
        ).exists():
            raise PermissionDenied
        return goal


class CommentSerializer(serializers.ModelSerializer):
    user = ProfileSerializer(read_only=True)

    class Meta:
        model = Comment
        read_only_fields = ('id', 'created', 'updated', 'goal')
        fields = '__all__'

    def validate_goal(self, value: Goal) -> Goal:
        if value.status == Goal.Status.archived:
            raise serializers.ValidationError('not allowed in archived goal')
        if self.context['request'].user.id != value.user_id:
            raise serializers.ValidationError('not owner of goal')
        return value
