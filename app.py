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
from RecognizerFunction import recognizer, getEncodings, addEncodings
from datetime import datetime
from QueryData import getDayID,getScheduleID # Functions for QueryData in DB
from werkzeug.utils import secure_filename
from json import JSONEncoder

class NumpyArrayEncoder(JSONEncoder):
   def default(self, obj):
      if isinstance(obj, np.ndarray):
         return obj.tolist()
      return JSONEncoder.default(self, obj)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config.from_object(config['production'])

conexion=MySQL(app)

def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
      return jsonify({'message':str(ex)})

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
         person={'UserID':datos[0], 'LastName':datos[1], 'FirstName':datos[2]}   # Gettin UserID and Name
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
  
# Getting POST to check if the user has already a locker
@app.route('/CheckLocker', methods=['POST']) # CHECKING LOCKER-USER 

# FUNCTION TO RETRIEVE INFORMATION FROM LockersUsers TABLE
# This function needs the UserID and make a query in the table LockersUsers to check if the user has already a Locker
# The query "sql" returns the LockerStatus if exists for the User :
#  --> If not exists a record of the User means that does not have any locker, so assigns a new locker automatically (The first available)
#  --> If the User has a LockerStatus = 1 means that the User is using a locker and has not finished to used it, so assigns that locker
#  --> If the User has a LockerStatus = 2 means that already finished to use the last locker assigned, so assigns a new locker

def checklocker():
   try:
      UserID=request.json['UserID']  # Getting UserID from the json.request file
      cursor=conexion.connection.cursor()
      sql="SELECT LockerID, LockerUsed, PersonID, DateAndTime FROM LockersUsers AS Ordered_date WHERE DateAndTime=ANY(SELECT MAX(DateAndTime) FROM LockersUsers GROUP BY PersonID) AND PersonID='{0}'".format(UserID)
      cursor.execute(sql)
      LastLockerStatus=cursor.fetchone()  # Getting answer from the query
      
      if LastLockerStatus is None:
         #ASIGN NEW LOCKER
         openflag=0 # Just open locker option
         sql2="SELECT LockerID, LockerNum FROM Lockers WHERE LockerNum=(SELECT MIN(LockerNum) FROM Lockers WHERE Availability=1)" 
         cursor.execute(sql2)
         lockerfree=cursor.fetchone()
         lockerfreeJs={'LockerID': lockerfree[0], 'DirectionF':lockerfree[1]} # LockerID, Direction to be opened
         print(lockerfreeJs)
         return jsonify({'LockerFree':lockerfreeJs, 'Openflag': openflag}) # Lockers registered and Locker ID/Direction to be opened
      
      else:
         LastLocker=LastLockerStatus[1]
         
         if LastLocker==1:
            #ASIGN THE SAME LOCKER
            openflag=1 #Open locker and leave option
            lockerfree=LastLockerStatus[0]   #solo regresa la direccion porque es el mismo
            lockerfreeJs={'LockerID':LastLockerStatus[0], 'DirectionF':LastLockerStatus[1]}   # LockerID, Direction to be opened
            print(LastLockerStatus)
            return jsonify({'LockerFree': lockerfreeJs, 'Openflag': openflag})
        
         elif LastLocker==2:
            #ASIGN NEW LOCKER
            openflag=0 # Just open locker option
            sql2="SELECT LockerID, LockerNum FROM Lockers WHERE LockerNum=(SELECT MIN(LockerNum) FROM Lockers WHERE Availability=1)" 
            cursor.execute(sql2)
            lockerfree=cursor.fetchone()
            #lockerfree=LastLockerStatus[0]
            lockerfreeJs={'LockerID': lockerfree[0], 'DirectionF':lockerfree[1]} # LockerID, Direction to be opened
            print(lockerfreeJs)
            return jsonify({'LockerFree':lockerfreeJs, 'Openflag': openflag}) # Lockers registered and Locker ID/Direction to be opened
        
         else:
            return jsonify({'LockerFree': 'ERROR', 'Openflag': 'ERROR'})

   except Exception as ex:
      return jsonify({'message':'CHECK LOCKER ERROR'})
# Getting POST to update LockersUsers Table in the DB
@app.route('/updateRegister', methods=['POST']) # UPDATING DB BITACORA

# FUNCTION TO INSERT DATA WHEN A LOCKER IS OPENED (UserID, LockerID, DATE and TIME) IN LockersUsers TABLE (BITACORA)
# The function use the UserID, LockerID and Leaveflag to register when a locker is opened

def lockerUsability():
   try:
      cursor=conexion.connection.cursor()
      UserID=int(request.json['UserID']) # Getting UserID from the json.request file
      LockerID2 = request.json['LockerID']  # Getting LockerID from the json.request file
      Leaveflag=int(request.json['Leaveflag'])
      print(Leaveflag)

      if Leaveflag==1:    # The user will be still using the locker
         # INSERT DATA INTO THE TABLE (BITACORA)   
         sql3="CALL sp_updateLockerUsers(%s,%s,%s)"
         input_date=(UserID, LockerID2, Leaveflag)
         cursor.execute(sql3,input_date)
         conexion.connection.commit() #Updating Finished

         # UPDATE LOCKER STATUS 
         sql4="UPDATE Lockers SET Availability=2 WHERE LockerID='{0}'".format(LockerID2) #Locker NOT AVAILABLE
         cursor.execute(sql4)
         conexion.connection.commit() #Updating Finished
         return jsonify({'message':'Registro Done'})

      else:    # The user won´t use the locker anymore (Leave the building)
            
         # INSERT DATA INTO THE TABLE (BITACORA)   
         sql5="CALL sp_updateLockerUsers(%s,%s,%s)"
         input_date2=(UserID, LockerID2, Leaveflag)
         cursor.execute(sql5,input_date2)
         conexion.connection.commit() #Updating Finished
            
         # UPDATE LOCKER STATUS
         sql6="UPDATE Lockers SET Availability=1 WHERE LockerID='{0}'".format(LockerID2)  # Locker IS AVAILABLE NOW
         cursor.execute(sql6)
         conexion.connection.commit() # Updating Finished
         return jsonify({'message':'Registro Done'})

      print("User registered successfully") 
      return jsonify({'message':'Registro Done'}) 

   except Exception as ex:
      return jsonify({'message':'LOCKER ERROR'})


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


@app.route('/registrationL', methods=['POST'])   # Getting POST request from Raspberry Pi Laboratory

# FUNCTION FOR LABORATORY REGISTRATION
def registrationL():
   try:
      cursor=conexion.connection.cursor()
      UserID=int(request.json['UserID']) # Getting UserID from the json.request file
      LaboratoryID =int(request.json['LaboratoryID'])  # Getting LockerID from the json.request file
      # User has a registration?
      sql1="call sp_registration(%s,%s)"
      sql1_input=(LaboratoryID, UserID)
      cursor.execute(sql1, sql1_input)
      Lesson=cursor.fetchone() #All data

      if Lesson !=None:
         print("hay clase")
      
         #Query RecordsManufactura if the user has '1' or '2' or ANY flag for the laboratory
         sql= "SELECT EntranceFlag FROM RecordsManufactura AS Ordered_date WHERE DateAndTime=ANY(SELECT MAX(DateAndTime) FROM RecordsManufactura GROUP BY PersonID) AND PersonID='{0}'".format(UserID)
         cursor.execute(sql)
         datos=cursor.fetchone()
         
         if datos ==None:     # NO REGISTRATION YET
            sql2="CALL sp_updateRegistration(%s,%s)"  # INSERT a new registration
            sql2_input=(UserID, 1)   # '1' for first registration
            cursor.execute(sql2,sql2_input)
            conexion.connection.commit() #Updating Finished
            return jsonify({'message':'Registration done', 'EntranceFlag':1})
         else: 
            flagE=datos[0]    # Reading the flag of the registration
            print(flagE)
            if flagE==2:      # The last entrance of the User has finished --> Insert a new registration 
               sql2="CALL sp_updateRegistration(%s,%s)" 
               sql2_input=(UserID, 1)   # '1' for first registration
               cursor.execute(sql2,sql2_input)
               conexion.connection.commit() # Update Finished
               return jsonify({'message':'Registration done', 'EntranceFlag':1})

            else:
               # UPDATE ENTRANCE STATUS--> EntranceFlag = 1 so the User will leave the laboratory
               sql3="CALL sp_updateRegistration(%s,%s)" 
               sql3_input=(UserID, 2)   # '1' for first registration
               cursor.execute(sql3,sql3_input)
               conexion.connection.commit() # Update Finished
               return jsonify({'message':'Registration done', 'EntranceFlag':2})
      else:
         print ("No hay clase")

         #INSER TO DENIED ACCESS
         return jsonify({'message':'ACCESO NEGADO'})

   except Exception as ex:
      return jsonify({'message':'LABORATORY REGISTRATION ERROR'})

@app.route('/BuildingAccess', methods=['POST'])   # Getting POST request from Raspberry Pi Laboratory

# FUNCTION FOR LABORATORY REGISTRATION
def BuildingAccess():
   try:
      cursor=conexion.connection.cursor()
      UserID=int(request.json['UserID']) # Getting UserID from the json.request file
      #UpdateDB for RecordsEntrance
      #Query RecordsEntrance if the user has '1' or '2' or ANY flag for the Entrance
      sql= "SELECT EntranceFlag FROM RecordsEntrance AS Ordered_date WHERE DateAndTime=ANY(SELECT MAX(DateAndTime) FROM RecordsEntrance GROUP BY PersonID) AND PersonID='{0}'".format(UserID)
      cursor.execute(sql)
      datos=cursor.fetchone()
      print(datos)
         
      if datos ==None:     # NO REGISTRATION YET
         sql2="CALL sp_updateBuildingAccess(%s,%s)"  # INSERT a new registration
         sql2_input=(UserID, 1)   # '1' for first registration
         cursor.execute(sql2,sql2_input)
         conexion.connection.commit() #Updating Finished
         return jsonify({'message':'Registration done', 'EntranceFlag':1})
      else: 
         flagE=datos[0]    # Reading the flag of the registration
         print(flagE)
         if flagE==2:      # The last entrance of the User has finished --> Insert a new registration 
            sql2="CALL sp_updateBuildingAccess(%s,%s)" 
            sql2_input=(UserID, 1)   # '1' for first registration
            cursor.execute(sql2,sql2_input)
            conexion.connection.commit() # Update Finished
            return jsonify({'message':'Registration done', 'EntranceFlag':1})

         else:
            # UPDATE ENTRANCE STATUS--> EntranceFlag = 1 so the User will leave the building
            sql3="CALL sp_updateBuildingAccess(%s,%s)" 
            sql3_input=(UserID, 2)   # '1' for first registration
            cursor.execute(sql3,sql3_input)
            conexion.connection.commit() # Update Finished
            return jsonify({'message':'Registration done', 'EntranceFlag':2})

   except Exception as ex:
      return jsonify({'message':'BUILDING REGISTRATION ERROR'})
   

@app.route('/GetEncondings', methods=['POST']) 
def GenerateEncodings():
   if 'file' not in request.files:
      return jsonify({'status':False,'message':'No file uploaded.'})
   file = request.files['file']
   if file.filename == '':
      return jsonify({'status':False,'message':'No file uploaded.'})
   if file and allowed_file(file.filename):
      filename = secure_filename(file.filename)
      filename = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
      file.save(filename)
      encodings = getEncodings(filename)
      os.remove(filename)
      if len(encodings) == 0:
         return jsonify({'status':False,'message':'No face detected.'}) 
      data = {'status':True,'message':'OK', 'encodings': encodings[0]}
      return jsonify(json.dumps(data, cls=NumpyArrayEncoder))


@app.route('/AddEncondings', methods=['POST']) 
def AddEncodings():
   UserID = int(request.json['UserID'])
   encs = request.json['encoding']
   encodings=np.asarray(encs)
   res = addEncodings(UserID, encodings)
   return jsonify({'status':res})  


def page_no_found(error):
   return "<h1>La pagina que intentas buscar no existe...</h1>", 404
  

if __name__ == "__main__":
   app.config.from_object(config['production'])
   app.register_error_handler(404,page_no_found)
   app.run(host='0.0.0.0',port=5100)
