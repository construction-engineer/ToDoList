import secrets
import string

from django.conf import settings
from django.core.management import BaseCommand

from todolist.bot.models import TgUser
from todolist.bot.tg.client import TgClient
from todolist.bot.tg.schemas import Message
from todolist.goals.models import Goal, GoalCategory

selected_category = {}


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tg_client = TgClient(settings.BOT_TOKEN)

    def handle(self, *args, **options):
        offset = 0
        try:
            while True:
                res = self.tg_client.get_updates(offset=offset)
                for item in res.result:
                    offset = item.update_id + 1
                    if item.message is not None:
                        self.handle_message(item.message)
        except Exception as e:
            print(f"An error occurred: {e}")

    def handle_message(self, msg: Message):
        tg_user, created = TgUser.objects.get_or_create(chat_id=msg.chat.id)
        if not tg_user.user:
            # User doesn't exist for this bot
            self.handle_unauthorized_user(tg_user, msg)
        else:
            # User exist for this bot
            self.handle_authorized_user(tg_user, msg)

    def handle_unauthorized_user(self, tg_user: TgUser, msg: Message):
        self.tg_client.send_message(msg.chat.id, f'Hi, @{msg.chat.username}')
        verification_code = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(16))
        tg_user.verification_code = verification_code
        tg_user.save(update_fields=['verification_code'])
        self.tg_client.send_message(msg.chat.id,
                                    f'Please confirm your account on taskboard.ga with this code:\n{verification_code}'
                                    )

    def handle_authorized_user(self, tg_user: TgUser, msg: Message):
        if msg.text.startswith('/'):
            self.handle_command(tg_user, msg.text)
        else:
            if category := selected_category.get(tg_user.chat_id):
                goal = Goal.objects.create(
                    title=msg.text,
                    category=category,
                    user=tg_user.user,
                )
                url = f"taskboard.ga/boards/{goal.category.board_id}/categories/{goal.category.id}/goals?goal={goal.id}"
                self.tg_client.send_message(msg.chat.id, f"Goal '{goal.title}' created:\n{url}")
                del selected_category[tg_user.chat_id]
                return
            if input_cat := GoalCategory.objects.filter(title=msg.text).first():
                selected_category[tg_user.chat_id] = input_cat
            self.handle_command(tg_user, '/selected_category')
            self.handle_command(tg_user, '/create')

    def handle_command(self, tg_user: TgUser, command: str):
        if command == '/goals':
            goals = Goal.objects.select_related('user').filter(
                category__board__participants__user=tg_user.user,
                category__is_deleted=False).exclude(status=Goal.Status.archived)
            if not goals:
                self.tg_client.send_message(tg_user.chat_id, "Goals isn't exist")
                return
            resp = "\n".join(goal.title for goal in goals)
            self.tg_client.send_message(tg_user.chat_id, resp)

        elif command == '/create':
            if not selected_category.get(tg_user.chat_id):
                categories = GoalCategory.objects.prefetch_related('board__participants').filter(
                    board__participants__user=tg_user.user,
                    is_deleted=False,
                )
                if not categories:
                    self.tg_client.send_message(tg_user.chat_id, "Categories isn't exist")
                    return
                resp = "\n".join(category.title for category in categories)
                self.tg_client.send_message(tg_user.chat_id, f"Select from existing categories:\n{resp}")
                return
            self.tg_client.send_message(tg_user.chat_id, "Enter your goal")

        elif command == '/selected_category':
            if not selected_category:
                self.tg_client.send_message(tg_user.chat_id, "You didn't select category to create goal")
                return
            self.tg_client.send_message(
                tg_user.chat_id,
                f"Selected category: {selected_category[tg_user.chat_id].title}"
                )

        elif command == '/cancel':
            selected_category.pop(tg_user.chat_id, None)
            self.tg_client.send_message(tg_user.chat_id, "You cancel the action")

        else:
            self.tg_client.send_message(tg_user.chat_id, "Unknown command")
