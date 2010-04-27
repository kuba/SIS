from formencode import Schema, ForEach, NestedVariables
from formencode.validators import DateConverter, Int

class AddLuckyNumberForm(Schema):
    date = DateConverter(month_style='dd/mm/yyyy')
    number = Int()

class AddLuckyNumbersForm(Schema):
    pre_validators = [NestedVariables()]
    allow_extra_fields = True
    filter_extra_fields = True
    lucky = ForEach(AddLuckyNumberForm())
