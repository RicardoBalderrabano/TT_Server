from flask import Flask,jsonify

from config_app import config
from flask_mysqldb import MySQL

  

app = Flask(__name__)

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

@app.route('/encodings', methods=['POST'])
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
     
def page_no_found(error):
   return "<h1>La pagina que intentas buscar no existe...</h1>", 404
  

if __name__ == "__main__":
   app.config.from_object(config['development'])
   app.register_error_handler(404,page_no_found)
   app.run(host='0.0.0.0',port=80)