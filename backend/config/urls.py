"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from apps.cards.urls import media_urlpatterns, prompt_urlpatterns, analysis_urlpatterns, deck_urlpatterns, token_urlpatterns


# Health check endpoint
def health_check(request):
    return JsonResponse({'status': 'ok', 'message': 'Backend is running'})


urlpatterns = [
    path('health', health_check, name='health-check'),
    path('health/', health_check, name='health-check-slash'),
    path('api/health/', health_check, name='api-health-check'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/user/', include('apps.users.urls')),
    path('api/words/', include('apps.words.urls')),
    path('api/cards/', include('apps.cards.urls')),
    path('api/media/', include((media_urlpatterns, 'media'), namespace='media')),
    path('api/user/', include((prompt_urlpatterns, 'prompts'), namespace='prompts')),
    path('api/cards/', include((analysis_urlpatterns, 'analysis'), namespace='analysis')),
    path('api/cards/', include((deck_urlpatterns, 'decks'), namespace='decks')),
    path('api/', include((token_urlpatterns, 'tokens'), namespace='tokens')),
    # API root для проверки
    path('api/', include('rest_framework.urls')),
]

# Serve media files
from django.views.static import serve
from django.urls import re_path

# Serve media files in both development and production
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
