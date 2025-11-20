from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/activities/', consumers.ActivityConsumer.as_asgi(), name='activities_ws'),
]
