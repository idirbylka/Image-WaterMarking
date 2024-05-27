import io

from flask import Flask, render_template, redirect, url_for, request, flash, session, get_flashed_messages
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, Column, LargeBinary, String
from sqlalchemy.orm import DeclarativeBase
from forms import FileUpload
from PIL import Image as PILImage, ImageDraw, ImageFont
import io
import base64


app = Flask(__name__)
app.secret_key = "ghl3lu76gsh8"
bootstrap = Bootstrap5(app)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///images.db"
db = SQLAlchemy(model_class=Base)

db.init_app(app)


# Image database creation
class Image(db.Model):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    data = Column(LargeBinary)


with app.app_context():
    db.create_all()


# Adding watermarks function
def add_watermark(image_data):
    image = PILImage.open(io.BytesIO(image_data))

    # ensuring the image is in RGBA mode
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=45)
    text = "WaterMark Pro"

    # Set the transparency level of the Watermarks
    transparency = 220

    # Get the text bounding box to determine the size
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
    image_width, image_height = image.size

    # loop to draw watermarks many times over the whole image
    for y in range(0, image_height, text_height + 120):
        for x in range(0, image_width, text_width + 120):
            draw.text(
                (x, y),
                text,
                fill=(255, 255, 255, transparency),
                stroke_width=0,
                stroke_fill="black",
                font=font)

    # Determine the format of the image
    output_format = image.format if image.format else "PNG"

    output = io.BytesIO()
    image.save(output, format=output_format)
    return output.getvalue()


@app.route("/")
def home():
    messages = get_flashed_messages(with_categories=True)
    return render_template("index.html", messages=messages)


@app.route("/upload_image", methods=["GET", "POST"])
def upload_image():
    form = FileUpload()
    if request.method == "POST" and form.validate_on_submit():

        if "upload_file" not in request.files:
            return "File nonexistent"

        file = request.files["upload_file"]

        if file.filename == "":
            return "No selected file"

        if file:
            file_data = file.read()
            try:
                watermarked_data = add_watermark(file_data)
            except Exception as e:
                flash(f"Error processing image: {str(e)}", "danger")
                return redirect(url_for("upload_image"))

            # image_base64 = base64.b64encode(watermarked_data).decode("utf-8")
            # session["image_base64"] = image_base64

            image_number = db.session.query(Image).count() + 1
            new_image = Image(
                name=f"image{image_number}",
                data=watermarked_data
            )

            db.session.add(new_image)
            db.session.commit()
            return redirect(url_for("view_image", image_id=new_image.id))
    return render_template("image-upload.html", form=form)


@app.route("/delete_image", methods=["POST"])
def delete_image():
    if "image_id" in session:
        image_id = session.pop("image_id", None)
        image = Image.query.get(image_id)
        if image:
            db.session.delete(image)
            db.session.commit()
        flash("Image deleted successfully!", "success")
    return redirect(url_for("home"))


@app.route("/view_image/<int:image_id>")
def view_image(image_id):
    image = Image.query.get_or_404(image_id)
    session["image_id"] = image_id
    image_base64 = base64.b64encode(image.data).decode("utf-8")
    return render_template("view_image.html", image_base64=image_base64)


if __name__ == "__main__":
    app.run(debug=True)
