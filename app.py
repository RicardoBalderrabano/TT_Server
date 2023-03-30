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
from datetime import datetime


app = Flask(__name__)

conexion=MySQL(app)

# TEST FUNCTION
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

# TEST FUNCTION
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

       
# Getting POST request from Raspberry Pi (Encoding)
@app.route('/encodings', methods=['POST'])   

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

# Getting POST FOR LOCKER STATUS
@app.route('/Lockers_Status', methods=['POST'])   
# FUNCTION - GET ALL THE LOCKER´S DIRECTION REGISTERED
def LockerStatus():
   
   cursor=conexion.connection.cursor()
   sql="SELECT LockerNum, LockerID, LockerRetro FROM Lockers" #Records to select
   cursor.execute(sql)
   lockers=cursor.fetchall() #All data
   lockall=[]
   for row in lockers:  #Extract all the lockers
         lockersJs={'Number':row[0], 'Direction':row[1], 'Retro': row[2]}
         lockall.append(lockersJs)  #Append every locker in a json file
   # Select the locker available (MIN)      
   sql2="SELECT LockerID, LockerNum FROM Lockers WHERE LockerNum=(SELECT MIN(LockerNum) FROM Lockers WHERE Availability=1)" 
   cursor.execute(sql2)
   lockerfree=cursor.fetchone()
   lockerfreeJs={'LockerID': lockerfree[0], 'DirectionF':lockerfree[1]} # LockerID, Direction to be opened
   return jsonify({'Lockers': lockall, 'LockerFree':lockerfreeJs}) # Lockers registered and Locker ID/Direction to be opened
  
# Getting POST to check user locker
@app.route('/CheckLocker', methods=['POST']) # CHECKING LOCKER-USER 
# FUNCTION TO RETRIEVE INFROMATION OF LockersUsers TABLE
def checklocker():
   
      UserID=request.json['UserID']  # Getting UserID from the json.request file
      print(UserID)
      cursor=conexion.connection.cursor()
      sql="SELECT LockerID, LockerUsed, PersonID, DateAndTime FROM LockersUsers AS Ordered_date WHERE DateAndTime=ANY(SELECT MAX(DateAndTime) FROM LockersUsers GROUP BY PersonID) AND PersonID='{0}'".format(UserID)
      cursor.execute(sql)
      LastLockerStatus=cursor.fetchone()
      #LastLocker=LastLockerStatus[1]
      if LastLockerStatus is None:
         #ASIGN NEW LOCKER
         openflag=0 # Just open locker option
         sql2="SELECT LockerID, LockerNum FROM Lockers WHERE LockerNum=(SELECT MIN(LockerNum) FROM Lockers WHERE Availability=1)" 
         cursor.execute(sql2)
         lockerfree=cursor.fetchone()
         lockerfreeJs={'LockerID': lockerfree[0], 'DirectionF':lockerfree[1]} # LockerID, Direction to be opened
         return jsonify({'LockerFree':lockerfreeJs, 'Openflag': openflag}) # Lockers registered and Locker ID/Direction to be opened
      
      else:
         LastLocker=LastLockerStatus[1]
         if LastLocker==1:
            #ASIGN THE SAME LOCKER
            openflag=1 #Open locker and leave option
            lockerfree=LastLockerStatus[0]
            lockerfreeJs={'LockerID':lockerfree}
            return jsonify({'LockerFree': lockerfreeJs, 'Openflag': openflag})
         elif LastLocker==2:
            #ASIGN NEW LOCKER
            openflag=0 # Just open locker option
            sql2="SELECT LockerID, LockerNum FROM Lockers WHERE LockerNum=(SELECT MIN(LockerNum) FROM Lockers WHERE Availability=1)" 
            cursor.execute(sql2)
            lockerfree=cursor.fetchone()
            lockerfree=LastLockerStatus[0]
            lockerfreeJs={'LockerID': lockerfree, 'DirectionF':lockerfree[1]} # LockerID, Direction to be opened
            return jsonify({'LockerFree':lockerfreeJs, 'Openflag': openflag}) # Lockers registered and Locker ID/Direction to be opened
         else:
            return jsonify({'LockerFree': 'ERROR', 'Openflag': 'ERROR'})

# Getting POST to update LockersUsers Table in the DB
@app.route('/updateRegister', methods=['POST']) # UPDATING DB BITACORA
# FUNCTION FOR INSERT DATA WHEN A LOCKER IS OPENED (UserID, LockerID, DATE and TIME)
def lockerUsability():
   #try:
      now=datetime.now()   # Getting date and time from the server
      formatted_date=now.strftime('%Y-%m-%d %H:%M:%S') # Setting format of the data and time 
      cursor=conexion.connection.cursor()
      UserID=int(request.json['UserID']) # Getting UserID from the json.request file
      LockerID2 = request.json['LockerID']  # Getting LockerID from the json.request file
      Leaveflag=int(request.json['Leaveflag'])
      print(Leaveflag)
      if Leaveflag==1:
         # INSERT DATA INTO THE TABLE (Instruction)   
         sql3="INSERT LockersUsers (LockerID, PersonID, DateAndTime, LockerUsed) VALUES (%s,%s,%s,%s)"
         input_date=(LockerID2, UserID, formatted_date, Leaveflag)
         cursor.execute(sql3,input_date)
         conexion.connection.commit() #Updating Finished
         # UPDATE LOCKER STATUS
         sql4="UPDATE Lockers SET Availability=2 WHERE LockerID='{0}'".format(LockerID2)
         cursor.execute(sql4)
         conexion.connection.commit() #Updating Finishe
         return jsonify({'message':'Registro Done'})
      else:
         print('Aqui')
         print(LockerID2)
         print(UserID)
         print(formatted_date)
         print(Leaveflag)
         
         sql5="INSERT LockersUsers (LockerID, PersonID, DateAndTime, LockerUsed) VALUES (%s,%s,%s,%s)"
         input_date2=(LockerID2, UserID, formatted_date, Leaveflag)
         cursor.execute(sql5,input_date2)
         conexion.connection.commit() #Updating Finished'''
         
         # UPDATE LOCKER STATUS
         sql6="UPDATE Lockers SET Availability=1 WHERE LockerID='{0}'".format(LockerID2)
         cursor.execute(sql6)
         conexion.connection.commit() #Updating Finished
         return jsonify({'message':'Registro Done'})

      
      #conexion.connection.commit() #Updating Finished 
      print("User registered successfully")
      return jsonify({'message':'Registro Done'}) 
   


@app.route('/encodings/Lockers', methods=['POST'])   # Getting POST request from Raspberry Pi Lockers (Encoding)

# FUNCTION FOR FACE RECOGNITION
def facerecognitionLockers():
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
         person={'UserID':datos[0], 'LastName':datos[1], 'FirstName':datos[2]}
         return jsonify({'person':person, 'message':'UserFound'})
      else:
         return jsonify({'message':'UserNoFound'})

   except Exception as ex:
      return jsonify({'message':'FACE RECOGNITION ERROR'})

def page_no_found(error):
   return "<h1>La pagina que intentas buscar no existe...</h1>", 404
  

if __name__ == "__main__":
   app.config.from_object(config['development'])
   app.register_error_handler(404,page_no_found)
   app.run(host='0.0.0.0',port=80)