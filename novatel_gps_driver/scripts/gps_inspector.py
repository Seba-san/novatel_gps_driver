#!/usr/bin/env python
# Revision $Id$
## Simple talker demo that published std_msgs/Strings messages
## to the 'chatter' topic
# La idea de este nodo es subscribirse y publicar mensajes.
# Version 1.0

import rospy
#import math
from math import sqrt
#from std_msgs.msg import String
from novatel_gps_msgs.msg import NovatelXYZ  # importante pone .msg
import statistics as st

#import numpy as np
import numpy as np

# Me baso en el tutorial:  http://wiki.ros.org/ROS/Tutorials/WritingPublisherSubscriber%28python%29
Historia=np.zeros((3,10))
Historia_desvios=np.zeros((20,1))
class Movimiento:
    x=0
    y=0
    z=0
    tot=0
   


Mov2=Movimiento()

    
        
    
    
    
def callback(datos):
#    rospy.loginfo(rospy.get_caller_id() + "I heard") # Manda al archivo log esta info
    #http://wiki.ros.org/rospy/Overview/Logging
#    Mensaje=NovatelXYZ.x
    # position_type: "Single" =Solution calculated using only data supplied by the GNSS satellites
    global Mov2, Historia, Movimiento, Historia_desvios
    
    desvio=np.zeros((3,1))
    
    
    class Vel:
        x=np.zeros((1,9))
        y=x
        z=x
        
    Mov=sqrt(datos.x**2+datos.y**2+datos.z**2) # Calculo la norma del vector movimiento
#    print("en x " + str(datos.x-Mov2.x) + " en y  "  + str(datos.y-Mov2.y) + " en z  " \
#          + str(datos.z-Mov2.z) + " total  " + str(Mov-Mov2.tot))
    Mov2.tot=Mov
    Mov2.x=datos.x 
    Mov2.y=datos.y 
    Mov2.z=datos.z 
    Satelites=datos.num_satellites_used_in_solution
    # Guardado de datos historicos
    Historia= np.roll(Historia,1,axis=1) 
    Historia[0][0]=datos.x 
    Historia[1][0]=datos.y 
    Historia[2][0]=datos.z 
    # Calculo del salto de cada lectura
    Vel.x=np.diff(Historia[0,:])
    Vel.y=np.diff(Historia[1,:])
    Vel.z=np.diff(Historia[2,:])
    # Desvio estandar de los saltos
    desvio[0]=datos.x_sigma
    desvio[1]=datos.y_sigma
    desvio[2]=datos.z_sigma
    desvio_novatel=max(desvio)
    desvio[0]=st.stdev(Vel.x)
    desvio[1]=st.stdev(Vel.x)
    desvio[2]=st.stdev(Vel.x)
    # Almacenamiento de la norma (noma max) de los desvios
    Historia_desvios= np.roll(Historia_desvios,1,axis=0)
    Historia_desvios[0]=max(desvio)
    # Promediado del desvio de las normas
    prom=sum(Historia_desvios)/len(Historia_desvios)
#    print("stdev prom vel " + str(prom) + " " + str(Satelites) + " sat " + str(desvio_novatel) + " stdev vel instantaneo (novatel)")
    if prom>1:
        rospy.logerr("GPS con mucha incertidumbre, stdev velocidad prom : %s m/s", str(prom*10))
#        print(str(Historia_desvios))
        
    if Satelites<6:
        rospy.logwarn("Pocos satelites visibles. Cantidad observada: %s",str(Satelites))
        
    if prom==0:
        rospy.logwarn("Sin informacion nueva; cantidad de satelites: %s",str(Satelites))
#        if prom>100:
#            rospy.logfatal("GPS con mucho desvio, val ref:%s", str(prom))
##    print(str(sum(Historia_desvios[:,0])))
#    print(str(desvio[0])+" "+ str(std_media(Vel.x)))
#    desvio=st.stdev(Historia2[0,:])
#    print(str(desvio))
#    print(str(desvio))
        
        
    
def std_media(datos):
    # Por sugerencia de Javier, calculo del desvio con la mediana
#    mediana=st.mean(datos)
    mediana=st.median(datos)
    sin_mediana=datos-mediana
    aux=np.sqrt(sum(sin_mediana**2)/(len(sin_mediana)-1))
    return aux


def gps_check():
    rospy.init_node('gps_check',anonymous=True)
    rospy.Subscriber("bestxyz",NovatelXYZ, callback) # cada vez que bestxyz publica, va a la funcion callback
    rospy.spin()


if __name__ == '__main__':
    gps_check()





#def talker():
#    pub = rospy.Publisher('chatter', String, queue_size=10)
#    rospy.init_node('talker', anonymous=True)
#    rate = rospy.Rate(10) # 10hz
#    while not rospy.is_shutdown():
#        hello_str = "hello world %s" % rospy.get_time()
#        rospy.loginfo(hello_str)
#        pub.publish(hello_str)
#        rate.sleep()
#
#if __name__ == '__main__':
#    try:
#        talker()
#    except rospy.ROSInterruptException:
#        pass
