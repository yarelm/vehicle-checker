import io
import os
import cv2
import re
from google.cloud import vision 
from datetime import datetime
from google.cloud import storage
import numpy as np
from flask import Flask, request
from PIL import Image, ImageFilter

app = Flask(__name__)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return recognise_license_plate()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def recognise_license_plate():
    bucket_name = request.args.get('bucket_name');
    img_file_name = request.args.get('img_file_name');
    print(bucket_name, img_file_name)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(img_file_name)
    file_bytes = blob.download_as_bytes()

    height = 800
    width = 600
    nparr = np.fromstring(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    img_color = cv2.imdecode(nparr, cv2.IMREAD_ANYCOLOR)
    img_str = cv2.imencode('.jpg', img)[1].tobytes()
    
    client = vision.ImageAnnotatorClient()

    response = client.annotate_image({
        'image': {'content': img_str},
    'features': [
        {'type_': vision.Feature.Type.OBJECT_LOCALIZATION},
        ]
    })

    height, width = img.shape[:2]

    vertices = []

    lo_annotations = response.localized_object_annotations
    for obj in lo_annotations:
        if obj.name == 'License plate' or obj.name == 'Vehicle Registration Plate':
            vertices = [(int(vertex.x * width), int(vertex.y * height)) for vertex in obj.bounding_poly.normalized_vertices]
            cv2.rectangle(img, vertices[0], vertices[2], (0, 255, 0), 3)


    if len(vertices) == 0:
        print('No license plate detected')
        return ''
    img_color = img_color[vertices[0][1]:vertices[2][1], vertices[0][0]:vertices[2][0]]

    cv2.imwrite("color.jpg", img_color)

    blob = bucket.blob("color.jpg")
    blob.upload_from_filename("color.jpg")

    mask_image=cv2.cvtColor(img_color,cv2.COLOR_BGR2HSV)

     # Create mask image with the only object as yellow color
    mask = cv2.inRange(mask_image,(20, 100, 20), (35, 255, 255) )

    ## morph-op to remove horizone lines
    kernel = np.ones((5,1), np.uint8)
    mask2 = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)

    ys, xs = np.nonzero(mask2)
    ymin, ymax = ys.min(), ys.max()
    xmin, xmax = xs.min(), xs.max()

    croped = img_color[ymin:ymax, xmin:xmax]

    cv2.imwrite("plate.jpg", croped)

    blob = bucket.blob("plate.jpg")
    blob.upload_from_filename("plate.jpg")

    with open('./plate.jpg', 'rb') as image_file:  # open colour image
        content = image_file.read()

    response = client.annotate_image({
        'image': {'content': content},
    'features': [
        {'type_': vision.Feature.Type.TEXT_DETECTION},
        ]
    })

    for text in response.text_annotations:
        plate = re.sub("[^0-9]", "", text.description)
        print('License plate is: ' + plate)
        return plate

