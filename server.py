import os
import secrets

import numpy as np
from flask import Flask, jsonify, request
import base64
from io import BytesIO
from flask_cors import CORS
from PIL import Image

import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import db

app = Flask(__name__)
CORS(app)
UserId = 0

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://faceattendancerealtime-c6597-default-rtdb.asia-southeast1.firebasedatabase.app/',
    'storageBucket': 'faceattendancerealtime-c6597.appspot.com'
})

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList

@app.route('/api/init_face', methods=['POST'])
def init_face():
    # Check if the request contains an image file
    if 'image' not in request.files:
        return jsonify({'valid': False, 'message': 'No image provided'})
    # Decode the base64-encoded image to a binary format
    image_data = base64.b64decode(request.form['image'])
    # Open the image file using Pillow
    image = Image.open(BytesIO(image_data))
    # Generate a unique 6-bit ID for the image file
    image_id = secrets.randbits(6)
    UserId = image_id
    # Save the image to a file in the 'Images' folder with the unique ID as the filename
    save_path = os.path.join('Images', f'{image_id}.png')
    image.save(save_path)

    # Importting student imgs
    folderPath = 'Images'
    pathList = os.listdir(folderPath)  # ['321654.png', '852741.png', '963852.png']
    print(pathList)
    imgList = []
    studentIds = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        print(path)
        print(os.path.splitext(path)[0])  # tach duoi file ra
        studentIds.append(os.path.splitext(path)[0])
        fileName = folderPath + '/' + path
        bucket = storage.bucket()
        blob = bucket.blob(fileName)
        blob.upload_from_filename(fileName)

    print("encoding started...")
    encodeListKnown = findEncodings(imgList)
    encodeListKnownWithIds = [encodeListKnown, studentIds]
    print("encoding complete")

    file = open("EncodeFile.p", 'wb')
    pickle.dump(encodeListKnownWithIds, file)
    file.close()
    print("file saved")


@app.route('/api/is_image_valid', methods=['POST'])
def is_image_valid():
    # Check if the request contains an image file
    if 'image' not in request.files:
        return jsonify({'valid': False, 'message': 'No image provided'})
    # Decode the base64-encoded image to a binary format
    image_data = base64.b64decode(request.form['image'])
    # Open the image file using Pillow
    image = Image.open(BytesIO(image_data))

    # Check if the image is valid
    try:
        # xu ly anh
        response = checkImage(image)
        return jsonify({'valid': response})
    except:
        return jsonify({'valid': False, 'message': 'Invalid image file'})


if __name__ == '__main__':
    app.run()


def checkImage(image):
    # load the encoding file
    print('loading encode file...')
    file = open("EncodeFile.p", 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    # print(studentIds)
    print('encode file loaded')

    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(img)
    encodeCurFrame = face_recognition.face_encodings(img, faceCurFrame)  # encode phan mat tren webcam
    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        # print("matches",matches)
        # print("faceDis",faceDis) #facedis cang thap thi cang giong

        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            # print("known face detected")
            # print(studentIds[matchIndex])
            id = studentIds[matchIndex]
            if id != UserId:
                return False
            else:
                return True

