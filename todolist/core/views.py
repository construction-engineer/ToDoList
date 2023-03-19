from rest_framework import generics

from todolist.core.serializers import CreateUserSerializer


class SignUpView(generics.CreateAPIView):
    serializer_class = CreateUserSerializer

