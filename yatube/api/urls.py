from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .views import (CommentViewSet, FollowViewSet, GroupViewSet, PostViewSet,
                    UserViewSet)

router = routers.DefaultRouter()
router.register('posts', PostViewSet)
router.register('groups', GroupViewSet)
router.register('users', UserViewSet)
router.register('follow', FollowViewSet, basename='follow')
router.register(r'posts/(?P<post_id>\d+)/comments',
                CommentViewSet, basename='post_comments'
                )

urlpatterns = [
    path('v1/', include(router.urls)),
    path(
        'v1/jwt/create/', TokenObtainPairView.as_view(),
        name='token_obtain_pair'
    ),
    path(
        'v1/jwt/refresh/', TokenRefreshView.as_view(),
        name='token_refresh'
    ),
    path(
        'v1/jwt/verify/', TokenVerifyView.as_view(),
        name='token_verify'
    ),
]
