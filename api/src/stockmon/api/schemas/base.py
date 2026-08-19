from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# Pydantic serializes plain Decimal fields to JSON as strings (e.g. "6.90"),
# which violates the contract's "raw numbers" rule. Money keeps Decimal math
# internally but serializes as a bare JSON number. Use only on response
# fields — request bodies keep plain Decimal (parsed safely from JSON numbers).
Money = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float, when_used="json")]
