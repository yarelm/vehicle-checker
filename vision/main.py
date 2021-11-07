import io
import os
import cv2
import re
from google.cloud import vision 
from datetime import datetime
from google.cloud import storage
import numpy as np
from flask import Flask, request

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
    img = img[vertices[0][1]:vertices[2][1], vertices[0][0]:vertices[2][0]]

    cv2.imwrite("plate.jpg", img)

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

