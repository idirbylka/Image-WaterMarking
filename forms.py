from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, URL


class FileUpload(FlaskForm):
    upload_file = FileField("Upload a File",
                            validators=[FileRequired(),
                                        FileAllowed(["jpg", "png", "jpeg", "pdf", "ico", "heic"],
                                                    "Images only!")])
    submit = SubmitField("Add Watermarks")


