# TT_Server
This repository contains the programs for the server of the TT.

The server of the Trabajo Terminal is used to proccess the information that the raspberry pi sends for the facial recognition and makes the connection with the Data Base of the users.

**S_recognizer.py
    --This file is in charge of make the facial recognition to the information that sent the raspberry pi (encodings of the faces). 
 
**facedatabase2.dat
    --This file contains the encodings of the faces that are trained in thje system and is used by "S_recognizer.py" to obtain the ID of the person that was detected by the raspberry pi.
    
**app.py
    --This file is used to make an API to make the connection with the DB of the system and receive the encodings from the raspberry pi.

**config_app.py
    --This file contains the configuration with the database of the system that is on the server. 
