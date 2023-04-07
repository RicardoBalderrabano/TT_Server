# This script contains the information to INSERT registration information about the lockers
# This query is gonna be changed by a stored procedure in the DB

import datetime
from datetime import datetime
import pytz

tz = pytz.timezone('America/Mexico_City')

def getDayID():
    # get cirrecnt datetime
    dt=datetime.now()
    # get day of week as an integer
    dateInt=dt.weekday()

    if dateInt ==0:     #Monday = 1
        DayID=1
    elif dateInt==1:    #Tuesday = 2
        DayID=2
    elif dateInt==2:    #Wednesday = 3
        DayID=3
    elif dateInt==3:    #Thursday = 4
        DayID=4
    elif dateInt==4:    #Friday = 5
        DayID=5
    elif dateInt==5:    #Saturday = 6
        DayID=6
    else:               #Sunday = 7
        DayID=7
    return DayID
   

def is_hour_between(start, end):
    # Time Now
    now=datetime.now(tz)
    now=now.strftime("%H:%M:%S")
    
    is_between = False
    is_between |= start <= now <= end
    is_between |= end <= start and (start <= now or now <= end)

    return is_between


def getScheduleID():
    if is_hour_between('06:50:00', '08:30:00')==True:       #7 am
        ScheduleID=1
    elif is_hour_between('08:20:00', '10:00:00')==True:     #8:30 am
        ScheduleID=2
    elif is_hour_between('09:50:00', '11:30:00')==True:     #10 am
        ScheduleID=3
    elif is_hour_between('11:20:00', '13:00:00')==True:     #11:30 am
        ScheduleID=4
    elif is_hour_between('12:50:00', '14:30:00')==True:     #1 pm
        ScheduleID=5
    elif is_hour_between('14:20:00', '16:00:00')==True:     #2:30 pm
        ScheduleID=6
    elif is_hour_between('15:50:00', '17:30:00')==True:     #4 pm
        ScheduleID=7
    elif is_hour_between('17:20:00', '19:00:00')==True:     #5:30 pm
        ScheduleID=8
    elif is_hour_between('18:50:00', '20:30:00')==True:     #7 pm
        ScheduleID=9
    elif is_hour_between('20:20:00', '10:00:00')==True:     #8:30 pm
        ScheduleID=10
    else:
        ScheduleID='error'
    return ScheduleID

