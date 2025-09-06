from rest_framework.routers import SimpleRouter
from .views import UserProfileViewset

app_name = 'users'

# Create router and register viewset
router = SimpleRouter()
router.register(r'profile', UserProfileViewset, basename='UserProfileViewset')

urlpatterns = router.urls
