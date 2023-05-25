from typing import Annotated
from fastapi import Depends


def inject(klass):
    return Annotated[klass, Depends()]
