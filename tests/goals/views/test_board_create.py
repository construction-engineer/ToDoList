from typing import Any
from unittest.mock import ANY

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from todolist.goals.models import Board


@pytest.mark.django_db
class TestBoardCreateView:
    url = reverse('todolist.goals:create-board')

    def test_create_unauthorized(self, client: APIClient, faker: Any) -> None:
        response = client.post(self.url, data=faker.pydict(1))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_deleted(self, auth_client: APIClient) -> None:
        response = auth_client.post(self.url, data={'is_deleted': True, })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Board.objects.last()

    def test_create_success(self, auth_client: APIClient) -> None:
        response = auth_client.post(self.url, data={'title': 'Board', })
        board = Board.objects.last()
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {
            'id': board.id,
            'created': ANY,
            'updated': ANY,
            'title': board.title,
            'is_deleted': board.is_deleted,
        }
