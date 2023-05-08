import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from todolist.goals.serializers import BoardCreateSerializer
from tests.factories import BoardFactory, UserFactory


@pytest.mark.django_db
class TestBoardsList:
    url = reverse('todolist.goals:list-board')

    def test_get_list_unauthorized(self, client: APIClient) -> None:
        response = client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_list_success(self, auth_client: APIClient, board_factory: BoardFactory, user: UserFactory) -> None:
        boards = board_factory.create_batch(size=2, with_owner=user)

        response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        for board in BoardCreateSerializer(boards, many=True).data:
            assert board in response.data["results"]

    def test_get_list_of_alien_boards(self, auth_client: APIClient, board_factory: BoardFactory) -> None:
        board_factory.create_batch(size=2)

        response = auth_client.get(self.url)

        assert response.data['count'] == 0
