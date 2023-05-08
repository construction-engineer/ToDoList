import random

import pytest
from django.contrib.auth.password_validation import CommonPasswordValidator, MinimumLengthValidator


@pytest.fixture(params=['min length validation', 'common password validation'])
def invalid_password(request, faker) -> str:
    if request.param == 'min length validation':
            return faker.password(length=random.randrange(4, MinimumLengthValidator().min_length))
    if request.param == 'common password validation':
            return CommonPasswordValidator().passwords.pop()
    if request.param == _:
            raise NotImplementedError
