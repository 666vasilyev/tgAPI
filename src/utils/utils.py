import inspect
from typing import Type

from fastapi import Form
from pydantic import BaseModel
from pydantic.fields import ModelField


def explode_link(link: str) -> dict[str, str]:
    channel_name, message_id = link.split('/')[-2:]
    return {
        "channel_name": channel_name,
        "message_id": message_id
    }

def as_form(cls: Type[BaseModel]):
    new_parameters = []

    for field_name, model_field in cls.__fields__.items():
        model_field: ModelField  # type: ignore

        new_parameters.append(
            inspect.Parameter(
                model_field.alias,
                inspect.Parameter.POSITIONAL_ONLY,
                default=Form(...) if model_field.required else Form(model_field.default),
                annotation=model_field.outer_type_,
            )
        )

    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, 'as_form', as_form_func)
    return cls


def process_reactions(reactions: list[tuple]) -> str:
    # Инициализируем счетчики положительных и отрицательных реакций
    positive_reactions_count = 0
    negative_reactions_count = 0

    for emoji, count in reactions:
        if emoji in ['👍', '❤️', '🔥', '🎉', '🤩', '😁', '🥰', '👏']:
            positive_reactions_count += count

        elif emoji in ['👎', '😱', '😢', '💩', '🤮', '🤯', '🤔', '🤬']:
            negative_reactions_count += count


    # Обновляем поле reaction для текущей записи
    return f"{positive_reactions_count}:{negative_reactions_count}"
