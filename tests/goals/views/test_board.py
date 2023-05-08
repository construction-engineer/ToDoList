import pytest
from django.urls import reverse
from rest_framework import status

from tests.utils import BaseTestCase
from todolist.goals.models import BoardParticipant, Goal, GoalCategory


@pytest.fixture()
def another_user(user_factory):
    return user_factory.create()


@pytest.mark.django_db ()
class TestRetrieveBoardView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, user):
        self.board = board_factory.create(with_owner=user)
        self.url = reverse('todolist.goals:board', args=[self.board.id])

    def test_auth_required(self, client):
        response = client.get(self.url, {})
        assert response.status_code != status.HTTP_200_OK

    def test_user_not_board_participant(self, client, another_user):
        assert not self.board.participants.filter(user=another_user).count()

        client.force_login(another_user)
        response = client.get(self.url)
        assert response.status_code != status.HTTP_200_OK

    def test_success(self, auth_client, user):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

        assert self.board.participants.count() == 1
        participant: BoardParticipant = self.board.participants.last()
        assert participant.user == user

        assert response.json() == {
            'id': self.board.id,
            'participants': [
                {
                    'id': participant.id,
                    'role': BoardParticipant.Role.owner.value,
                    'user': user.username,
                    'created': self.datetime_to_str(participant.created),
                    'updated': self.datetime_to_str(participant.updated),
                    'board': participant.board_id
                }
            ],
            'created': self.datetime_to_str(self.board.created),
            'updated': self.datetime_to_str(self.board.updated),
            'title': self.board.title,
            'is_deleted': False
        }


@pytest.mark.django_db()
class TestDestroyBoardView(BaseTestCase):

    @pytest.fixture(autouse=True)
    def setup(self, board_factory, goal_category_factory, goal_factory, user):
        self.board = board_factory.create(with_owner=user)
        self.url = reverse('todolist.goals:board', args=[self.board.id])
        self.cat: GoalCategory = goal_category_factory.create(board=self.board, user=user)
        self.goal: Goal = goal_factory.create(category=self.cat, user=user)
        self.participant: BoardParticipant = self.board.participants.last()

    def test_auth_required(self, client):
        response = client.delete(self.url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_success(self, auth_client):
        assert self.participant.role == BoardParticipant.Role.owner

        response = auth_client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        self.board.refresh_from_db(fields=('is_deleted',))
        self.cat.refresh_from_db(fields=('is_deleted',))
        self.goal.refresh_from_db(fields=('status',))
        assert self.board.is_deleted
        assert self.cat.is_deleted
        assert self.goal.status == Goal.Status.archived


@pytest.mark.django_db()
class TesUpdateBoardView(BaseTestCase):
    @pytest.fixture(autouse=True)
    def setup(self, board_factory, user):
        self.board = board_factory.create(with_owner=user)
        self.url = reverse('goals:board', args=[self.board.id])
        self.participant: BoardParticipant = self.board.participants.Last()

    @pytest.mark.parametrize('method', ['put', 'patch'])
    def test_auth_required(self, client, method):
        response = getattr(client, method)(self.urt, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize('method', ['put', 'patch'])
    def test_user_not_board_participant(self, client, another_user, method):
        assert not self.board.partioipants.filter(users=another_user).count()

        client.force_login(another_user)
        response = getattr(client, method)(self.urt)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        'user_role',
        [BoardParticipant.Role.writer, BoardParticipant.Role.reader],
        ids = ['writer', 'reader'],
    )
    def test_reader_or_writer_failed_to_update_board(self, faker, user_role, auth_client):
        self.participant.role = user_role
        self.participant.save(update_fields=('role',))
        response = auth_client.patch(self.url, faker.pydict(1))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_title_by_owner(self, auth_client, faker):
        assert self.participant.role == BoardParticipant.Role.owner
        new_title = faker.sentence()

        response = auth_client.patch(self.urt, {'title': new_title})
        assert response.status_code == status.HTTP_200_OK

        self.board.refresh_from_db(fields=('title',))
        assert self.board.title == new_title

    def test_desk_owner_can_not_change_itself_role(self, auth_client):
        assert self.participant.role == BoardParticipant.Role.owner

        response = auth_client.patch(self.url, {
            'participants': [
                {
                    'role': BoardParticipant.Role.writer,
                    'user': self.participant.user.username,
                }
            ],
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        self.participant.refresh_from_db()
        assert self.participant.role == BoardParticipant.Role.owner

    def test_failed_to_set_many_owners(self, auth_client, another_user):
        response = auth_client.patch(self.url, {
            'participants': [
                {
                    'role': BoardParticipant.Role.owner,
                    'user': self.participant.user.username,
                },
                {
                    'role': BoardParticipant.Role.owner,
                    'user': another_user.username,
                }
            ],
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert BoardParticipant.objects.count() == 1

    def test_failed_to_delete_all_participants_including_owner(self, auth_client):
        assert BoardParticipant.objects.count() == 1

        response = auth_client.patch(self.url, {
            'participants': [],
        })
        assert response.status_code == status.HTTP_200_OK
        assert BoardParticipant.objects.count() == 1

    @pytest.mark.parametrize('role', [
        BoardParticipant.Role.writer,
        BoardParticipant.Role.reader,
        ], ids=['writer', 'reader'])
    def test_only_owner_can_edit_board(self, client, another_user, faker, role):
        BoardParticipant.objects.create(board=self.board, user=another_user, role=role)

        client.force_login(another_user)
        response = client.patch(self.url, {'title': faker.sentence()})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_add_new_participant(self, auth_client, another_user):
        assert BoardParticipant.objects.count() == 1

        response = auth_client.patch(self.url, {
            'participants': [
                {
                    'role': BoardParticipant.Role.writer,
                    'user': another_user.username,
                }
            ],
        })
        assert response.status_code == status.HTTP_200_OK
        assert BoardParticipant.objects.count() == 2

    def test_delete_participant_from_board(self, auth_client, another_user):
        BoardParticipant.objects.create(
            board=self.board,
            user=another_user,
            role=BoardParticipant.Role.writer
        )

        response = auth_client.patch(self.url, {'participants': []})
        assert response.status_code == status.HTTP_200_OK
        assert BoardParticipant.objects.count() == 1

    def test_change_board_participant_role(self, auth_client, another_user):
        BoardParticipant.objects.create(
            board=self.board,
            user=another_user,
            role=BoardParticipant.Role.writer
        )

        response = auth_client.patch(self.urt, {'participants': [
            {
                'role': BoardParticipant.Role.reader,
                'user': another_user.username,
            }
        ]})

        assert response.status_code == status.HTTP_200_OK
        assert BoardParticipant.objects.count() == 2
