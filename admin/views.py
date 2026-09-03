from sqladmin import ModelView

from bot.database.models import Deadline, User


class UserAdmin(ModelView, model=User):
    name = "Ученик"
    name_plural = "Ученики"
    icon = "fa-solid fa-users"

    column_list = [User.id, User.telegram_id]
    column_labels = {User.id: "ID", User.telegram_id: "Telegram ID"}
    column_searchable_list = [User.telegram_id]
    column_sortable_list = [User.id, User.telegram_id]

    can_create = False
    can_edit = False
    can_delete = True
    can_export = True


class DeadlineAdmin(ModelView, model=Deadline):
    name = "Дедлайн"
    name_plural = "Дедлайны"
    icon = "fa-solid fa-clock"

    column_list = [Deadline.position, Deadline.due_date, Deadline.label]
    column_labels = {
        Deadline.position: "Порядок",
        Deadline.due_date: "Дата",
        Deadline.label: "Что сдаём",
    }
    column_sortable_list = [Deadline.position, Deadline.due_date]
    form_columns = ["label", "due_date", "position"]
    form_args = {
        "label": {"label": "Что сдаём (например: дедлайн по рекламе)"},
        "due_date": {"label": "Дата (ГГГГ-ММ-ДД)"},
        "position": {"label": "Порядок в списке"},
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_export = True
    name_plural = "Дедлайны"
