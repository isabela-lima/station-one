from datetime import date

import pytest
from pydantic import ValidationError

from schemas.items import ItemCreate, ItemUpdate


def test_due_date_is_a_calendar_day():
    assert ItemCreate(content="pagar fatura", due_date="2026-10-10").due_date == date(2026, 10, 10)


def test_due_date_rejects_garbage():
    with pytest.raises(ValidationError):
        ItemCreate(content="x", due_date="sexta")


def test_update_can_clear_due_date():
    # null explícito chega como campo enviado (o router usa exclude_unset)
    assert ItemUpdate(due_date=None).model_dump(exclude_unset=True) == {"due_date": None}
