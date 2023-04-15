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

from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)
UserId = -1

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


@app.route('/api/init_face', methods=["POST"], strict_slashes=False)
def init_face():
    image_data = request.json['image_data']
    # Remove the prefix using string slicing
    b64_image = image_data[22:]
    # Decode the Base64 string to bytes
    imgdata = base64.b64decode(b64_image)
    image_id = secrets.randbits(6)
    filename = f'{image_id}.png'
    # Save the image to a file
    with open(os.path.join('Images', filename), 'wb') as f:
        f.write(imgdata)

    # return jsonify({'valid': True, 'message': 'Image uploaded successfully'})
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


@app.route('/api/is_image_valid', methods=['POST'], strict_slashes=False)
def is_image_valid():
    image_data = request.json['image_data']
    # Remove the prefix using string slicing
    b64_image = image_data[22:]
    # Decode the Base64 string to bytes
    imgdata = base64.b64decode(b64_image)
    image_id = secrets.randbits(6)
    loadedImageFilename = f'{image_id}.png'
    # Save the image to a file
    with open(loadedImageFilename, 'wb') as f:
        f.write(imgdata)
    # Open the image file using Pillow
    image = cv2.imread(loadedImageFilename)

    # Check if the image is valid
    # xu ly anh
    # load the encoding file
    print('loading encode file...')
    file = open("EncodeFile.p", 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    # print(studentIds)
    print('encode file loaded')
    # img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(img)
    encodeCurFrame = face_recognition.face_encodings(img, faceCurFrame)  # encode phan mat tren webcam
    # delete file not used anymore
    if os.path.exists(loadedImageFilename):
        os.remove(loadedImageFilename)
    else:
        print("The file does not exist")

    jsonReturn = jsonify({'valid': False, 'message': 'Khong trung'})
    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        print("matches", matches)
        print("faceDis", faceDis)  # facedis cang thap thi cang giong
        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            print("known face detected")
            print(studentIds[matchIndex])
            jsonReturn = jsonify({'valid': True, 'message': 'Trung'})

    return jsonReturn


if __name__ == '__main__':
    app.run()
