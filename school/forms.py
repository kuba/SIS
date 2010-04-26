from formencode import Schema, ForEach, NestedVariables
from formencode.validators import DateConverter, Int

class AddOneLuckyNumber(Schema):
    date = DateConverter(month_style='dd/mm/yyyy')
    number = Int()

class AddWeekLuckyNumbersForm(Schema):
    pre_validators = [NestedVariables()]
    allow_extra_fields = True
    filter_extra_fields = True
    lucky = ForEach(AddOneLuckyNumber())
