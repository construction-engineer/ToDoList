from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from todolist.views import health_check

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('ping/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('core/', include(('todolist.core.urls', 'todolist.core'))),
    path('goals/', include(('todolist.goals.urls', 'todolist.goals'))),
    path('bot/', include(('todolist.bot.urls', 'todolist.bot'))),
]

if settings.DEBUG:
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls'))
    ]
