from flask import Flask, request, send_file, render_template
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
from rembg import remove, new_session # Better AI session
import io

app = Flask(__name__)
CORS(app)
# Background removal ke liye professional session
model_session = new_session("u2net")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    file = request.files['image']
    action = request.form['action']
    img = Image.open(file.stream)
    
    save_format = 'PNG'
    
    mimetype = 'image/png'
    download_name = 'processed_image.png'

    if action == 'remove_bg':
        # AI session ka use karke saaf edges paayein
        img = remove(img, session=model_session)
        bg_color = request.form.get('bg_color', 'transparent')
        if bg_color != 'transparent':
            background = Image.new('RGBA', img.size, bg_color)
            background.paste(img, (0, 0), img)
            img = background.convert('RGB')
        
    elif action == 'enhance':
        if img.mode != 'RGB':
            img = img.convert('RGB')
        # Remini style enhancement logic
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Sharpness(img).enhance(3.0)
        img = ImageEnhance.Color(img).enhance(1.3)
        img = img.filter(ImageFilter.DETAIL)

    elif action == 'resize':
        width = int(request.form['width'])
        height = int(request.form['height'])
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
    elif action == 'compress':
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        target_kb = float(request.form['target_kb'])
        target_bytes = target_kb * 1024
        save_format = 'JPEG'
        mimetype = 'image/jpeg'
        download_name = 'compressed_image.jpg'
        quality = 95
        img_io = io.BytesIO()
        img.save(img_io, format=save_format, quality=quality)
        while img_io.tell() > target_bytes and quality > 10:
            quality -= 5
            img_io = io.BytesIO()
            img.save(img_io, format=save_format, quality=quality)
        img_io.seek(0)
        return send_file(img_io, mimetype=mimetype, as_attachment=True, download_name=download_name)

    # Final image ko RAM (memory) mein save karke bhejna
    img_io = io.BytesIO()
    img.save(img_io, format=save_format)
    img_io.seek(0)
    return send_file(img_io, mimetype=mimetype, as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    app.run(debug=True)