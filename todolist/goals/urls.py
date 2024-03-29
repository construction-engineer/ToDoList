from django.urls import path

from todolist.goals import views


urlpatterns = [
    path('board/create', views.BoardCreateView.as_view(), name='create-board'),
    path('board/list', views.BoardListView.as_view(), name='list-board'),
    path('board/<int:pk>', views.BoardView.as_view(), name='board'),
    path("goal_category/create", views.GoalCategoryCreateView.as_view(), name="create-category"),
    path("goal_category/list", views.GoalCategoryListView.as_view(), name="list-goals"),
    path("goal_category/<int:pk>", views.GoalCategoryView.as_view(), name="goal-category"),
    path('goal/create', views.GoalCreateView.as_view(), name='create-goal'),
    path('goal/list', views.GoalListView.as_view(), name='goal-list'),
    path('goal/<int:pk>', views.GoalView.as_view(), name='goal'),
    path('goal_comment/create', views.CommentCreateView.as_view(), name='comment-create'),
    path('goal_comment/list', views.CommentListView.as_view(), name='comment-list'),
    path('goal_comment/<int:pk>', views.CommentView.as_view(), name='comment'),
]
