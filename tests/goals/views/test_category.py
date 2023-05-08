import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestCategoryRetrieve:
    def test_get_unauthorized(self, client: APIClient) -> None:
        url = reverse('todolist.goals:goal-category', args=[1])
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
