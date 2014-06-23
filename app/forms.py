from flask.ext.wtf import Form
from wtforms import TextField, SubmitField
from wtforms.validators import Required
    
class EditForm(Form):
    address = TextField('address', validators = [Required()])
    submit = SubmitField('Submit')
    