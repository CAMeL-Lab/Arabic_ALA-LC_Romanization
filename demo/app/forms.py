from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class RomanizeForm(FlaskForm):
    input_field = StringField('Input', validators=[DataRequired()])
    output_field = StringField('Output', validators=[])
    submit = SubmitField('Romanize')

