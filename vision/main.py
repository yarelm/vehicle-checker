import io
import os
import cv2
import re
from google.cloud import vision 
from datetime import datetime
from google.cloud import storage
import numpy as np
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return recognise_license_plate()
    # return "Hello {}!".format(name)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

def recognise_license_plate():
    # start_time =datetime.now()
    # img = cv2.imread(img_path)
    # height, width = img.shape[:2]
    # img = cv2.resize(img,(800, int((height*800)/width)))
    # cv2.imshow('Original image',img) 
    # cv2.imwrite(SOURCE_PATH+"output.jpg", img)
    # img_path= SOURCE_PATH+ "output.jpg"
    # client = vision.ImageAnnotatorClient()
    # with io.open(img_path, 'rb') as image_file:
    #     content = image_file.read()

    storage_client = storage.Client()
    bucket = storage_client.get_bucket('yarel-license-plate')
    blob = bucket.get_blob('img.jpg')
    file_bytes = blob.download_as_bytes()


    height = 800
    width = 600
    nparr = np.fromstring(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    # img = cv2.imread('301-F.jpg',cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img,(800, int((height*800)/width)))
    img_str = cv2.imencode('.jpg', img)[1].tobytes()
    # cv2.imwrite("output.jpg", img)
    
    client = vision.ImageAnnotatorClient()

    # with open('./output.jpg', 'rb') as image_file:
    #     content = image_file.read()

    response = client.annotate_image({
        'image': {'content': img_str},
    # 'image': {'source': {'image_uri': 'gs://yarel-license-plate/1635841842507.jpg'}},
    'features': [
        {'type_': vision.Feature.Type.OBJECT_LOCALIZATION},
        ]
    })

    # image = vision.types.Image(content=content)
    # response = client.text_detection(image=image)
    # texts=response.text_annotations

    # print(len(response.text_annotations))


    # for text in response.text_annotations:
    #     print(text)

    # print(len(response.localized_object_annotations))

    # for obj in response.localized_object_annotations:
    #     print(obj)

    

    # img = cv2.resize(img,(800, int((height*800)/width)))

    height, width = img.shape[:2]
    # img = cv2.resize(img,(800, int((height*800)/width)))

    # print(height, width)
    
    # print(response.localized_object_annotations)

    lo_annotations = response.localized_object_annotations
    for obj in lo_annotations:
        if obj.name == 'License plate' or obj.name == 'Vehicle Registration Plate':
            print(obj.bounding_poly.normalized_vertices)

            vertices = [(int(vertex.x * width), int(vertex.y * height)) for vertex in obj.bounding_poly.normalized_vertices]
            # vertices = [(vertex.x, vertex.y)
                        # for vertex in obj.bounding_poly.normalized_vertices]
            print('License ', vertices)
            cv2.rectangle(img, vertices[0], vertices[2], (0, 255, 0), 3)

            # LOGGER.debug('License plate detected: %s', vertices)


    # print(vertices[0], vertices[2])
    # print(img.shape)
    img = img[vertices[0][1]:vertices[2][1], vertices[0][0]:vertices[2][0]]

    cv2.imwrite("plate.jpg", img)

    with open('./plate.jpg', 'rb') as image_file:  # open colour image
        content = image_file.read()

    response = client.annotate_image({
        'image': {'content': content},
    # 'image': {'source': {'image_uri': 'gs://yarel-license-plate/1635841842507.jpg'}},
    'features': [
        {'type_': vision.Feature.Type.TEXT_DETECTION},
        ]
    })

    # print(len(response.text_annotations))


    for text in response.text_annotations:
        # print(text.description)
        plate = re.sub("[^0-9]", "", text.description)
        print('License plate is: ' + plate)
        return 'License plate is: ' + plate

        

    # cv2.imshow('image',img)
    # cv2.waitKey(0)

# recognise_license_plate()
