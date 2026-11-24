from typing import Annotated

from pydantic import StringConstraints

Amount = Annotated[
    str, StringConstraints(pattern=r"^(0|[1-9][0-9]{0,9})(\.[0-9]{1,2})?$")
]
