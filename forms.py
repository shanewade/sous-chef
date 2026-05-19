from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class RecipeForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=200, message="Title must be 200 characters or fewer."),
        ],
    )
    description = StringField("Description", validators=[Optional()])
    cook_time_minutes = IntegerField(
        "Cook Time (minutes)",
        validators=[
            Optional(),
            NumberRange(min=1, message="Cook time must be a positive number."),
        ],
    )
    servings = IntegerField(
        "Servings",
        validators=[
            Optional(),
            NumberRange(min=1, message="Servings must be a positive number."),
        ],
    )
    ingredients_text = TextAreaField("Ingredients", validators=[Optional()])
    steps = TextAreaField("Steps", validators=[Optional()])
    tags = StringField("Tags", validators=[Optional()])  # comma-separated, set by JS
    image_url = StringField("Image URL", validators=[Optional(), Length(max=500)])
