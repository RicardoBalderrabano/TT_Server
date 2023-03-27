import imutils
import cv2
import face_recognition
import pickle
import os
import numpy as np
from flask import Flask
from flask import jsonify # <- `jsonify` instead of `json`
from flask import request
from config_app import config
from flask_mysqldb import MySQL
import json
from RecognizerFunction import recognizer


app = Flask(__name__)
#encodingsJ=[{'encoding':'12 415 45 45'}]
conexion=MySQL(app)

@app.route('/users')
def list_users():
   try:
      cursor=conexion.connection.cursor()
      sql="SELECT PersonID, LastName, FirstName FROM Users"
      cursor.execute(sql)
      datos=cursor.fetchall()
      persons=[]
      for fila in datos:
         person={'ID':fila[0], 'LastName':fila[1], 'FirstName':fila[2]}
         persons.append(person)
      return jsonify({'persons':persons, 'message': 'Usuarios listados'})

   except Exception as ex:
      print(ex)
      return jsonify({'message':'x'})

@app.route('/users/<PersonID>', methods=['GET'])
def read_person(PersonID):
   try:
      cursor=conexion.connection.cursor()
      sql="SELECT PersonID, LastName, FirstName FROM Users WHERE PersonID = '{0}'".format(PersonID)
      cursor.execute(sql)
      datos=cursor.fetchone()
      if datos != None:
         person={'ID':datos[0], 'LastName':datos[1], 'FirstName':datos[2]}
         return jsonify({'person':person, 'message': 'Usuario encontrado'})
      else:
         return jsonify({'message': 'Usuario no encontrado'})
   except Exception as ex:
      return jsonify({'message':'ERROR 2'})

       

@app.route('/encodings', methods=['POST'])   # Getting POST request from Raspberry Pi (Encoding)

# FUNCTION FOR FACE RECOGNITION
def facerecognition():
   try:
      encs = request.json['encoding']  # Convert json "encodings" to array
      # Derialization of encoding recieved
      decodeArrays=json.loads(encs)
      finalNumpyArray=np.asarray(decodeArrays)
      # Convert Encoding array to a List of Array 
      encodings=[(finalNumpyArray)]
      # Inner Function for face recognition
      PersonID=recognizer(encodings)
      # Database connection
      cursor=conexion.connection.cursor()
      sql="SELECT PersonID, LastName, FirstName FROM Users WHERE PersonID = '{0}'".format(PersonID)
      cursor.execute(sql)
      datos=cursor.fetchone()
      if datos != None:
         person={'LastName':datos[1], 'FirstName':datos[2]}
         return jsonify({'person':person, 'message':'UserFound'})
      else:
         return jsonify({'message':'UserNoFound'})

   except Exception as ex:
      return jsonify({'message':'FACE RECOGNITION ERROR'})


'''
def addencodingsJ():

   FACEDB = "/home/ubuntu/tests/facedatabase2.dat"  # Direction of the database of trained faces
   
   file_dir = os.path.dirname(os.path.realpath(__file__))
   FACEDB = os.path.join(file_dir, FACEDB)
   FACEDB = os.path.abspath(os.path.realpath(FACEDB))

   encs = request.json['encoding']  # Convert json "encodings" to array
   
   # Derialization of encoding recieved
   decodeArrays=json.loads(encs)
   finalNumpyArray=np.asarray(decodeArrays)

   # Convert Encoding array to a List of Array 
   encodings=[(finalNumpyArray)]
   
   # Confidence 
   conf = 0.5
   maxImgs = 100

   # Load the faces database
   print("Loading faces database...")
   faceData = pickle.loads(open(FACEDB, "rb").read())
   userIDs = []

   for encoding in encodings:
      # attempt to match each face in the input image to our known
      # encodings
      matches = face_recognition.compare_faces(faceData["encodings"],
                                                   encoding, 0.5)
         # matches contains a list of True/False values indicating
         # which known_face_encodings match the face encoding to check
      id = "Unknown"
         # check to see if we have found a match i.e. we have at least
         # one True value in matches
      if True in matches:
         matchedIdxs = []
               # find the indexes of all matched faces then initialize a
               # dictionary to count the total number of times each face
               # was matched
         for (idx, value) in enumerate(matches):
               if value:
                  matchedIdxs.append(idx)
               
               counts = {}
               # loop over the matched indexes and maintain a count for
               # each recognized face
               for i in matchedIdxs:
                  id = faceData["ids"][i]
                  counts[id] = counts.get(id, 0) + 1
               # determine the recognized face with the largest number of
               # votes (note: in the event of an unlikely tie Python will
               # select first entry in the dictionary)
               id = max(counts, key=counts.get)
               if(counts[id] < (maxImgs * conf)):
                  id = "Unknown"

   # update the list of ids
   userIDs.append(id)

   # Database connection
   PersonID=id
   cursor=conexion.connection.cursor()
   sql="SELECT PersonID, LastName, FirstName FROM Users WHERE PersonID = '{0}'".format(PersonID)
   cursor.execute(sql)
   datos=cursor.fetchone()
   if datos != None:
      person={'LastName':datos[1], 'FirstName':datos[2]}
      return jsonify({'person':person, 'message':'UserFound'})
   else:
       return jsonify({'message':'UserNoFound'})
'''
def page_no_found(error):
   return "<h1>La pagina que intentas buscar no existe...</h1>", 404
  

if __name__ == "__main__":
   app.config.from_object(config['development'])
   app.register_error_handler(404,page_no_found)
   app.run(host='0.0.0.0',port=80)