from django.urls import path
from linting import views

urlpatterns = [
    path("", views.index, name="index"),
    path("validate", views.validate, name="validate"),
]
