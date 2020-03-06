#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 10:58:32 2020

@author: seba
"""

# Prueba con serial
# Recordar instalar la libreria serial
#pip install pyserial
#from serial import Serial
#python -m serial.tools.list_ports # Hace una lista de los puertos
import serial
import time
import numpy as np
import sys
import math
import statistics as st

puerto='/dev/ttyUSB0'
COM_base='com1'
COM_rover='com1'
COM_rb='com2'
debug=0

# ################################################## Declaracion de funciones
def timer_print(tiempo):
     k=0
     while k<tiempo:
        k=k+1
        time.sleep(1)
        print('\r                                 '),
        print('\rquedan: ' + str(tiempo-k)+' s'),
        sys.stdout.flush()
        
     print('\r')
        
def DEBUGUEANDO(encabezado,dato):
    if debug==1:
        print(encabezado+dato)
    
def Config_puerto():
    ser=serial.Serial()
    ser.baudrate=9600
    ser.port=puerto
    ser.timeout=1
    ser.open()
    time.sleep(1)
    if ser.isOpen()==False:
        print('Error, no se abrio el puerto serial')
    return ser

def Ver_inbuffer(ser):
    banderas=np.zeros((3,1))
    while ser.in_waiting>0:
        dato=ser.read_until()        
        if dato=='<OK\r\n':
            banderas[0]=1 # OK recibido
        
        elif dato=='[COM1]\r\n' or dato=='[COM1]':
            banderas[1]=1
            
        elif dato=='[COM2]\r\n' or dato=='[COM2]' :
            banderas[1]=2
        
        elif dato=='\r\n':# no hacer nada
             banderas[2]=-1  
        else:
            if debug:
                 print('Dato_rx: '+dato) 
            
    if banderas[0]==1:
        print('comando enviado correctamente al puerto COM'+str(int(banderas[1])))
    return banderas
            
    
def check_ok(banderas):
    if banderas[0]==1: #and banderas[1]!=0:
        return True
    return False
           
def Env_comando(ser,comando,check=True):
    # Con solo (CR), ver pag 190/650
    while True:
        comando2=comando+'\r'
        ser.write(comando2)
        DEBUGUEANDO('comando enviado: ',comando2)
        time.sleep(1)
        banderas=Ver_inbuffer(ser)
        aux=check_ok(banderas)
        if check==False or aux==True:
            return comando2,banderas
        
    return comando2,banderas

def Config_puente(ser):
    # Puente en rover
    # ## Conectar la PC en COM1, la radio en el COM2 y en la base conectar la radio en el COM2
    #INTERFACEMODE [port] rxtype txtype [responses]
#    INTERFACEMODE COM1 TCOM2 NONE OFF
    aux='t'+COM_rover
    Env_comando(ser,'interfacemode ' + COM_rb +' ' +  aux + ' none') # com2 como transceiver
    # Si lo configuras bidireccional no lo podes resetear.
#    aux='t'+COM_rb
#    Env_comando(ser,'interfacemode ' + COM_rb +' ' +  aux + ' none')  # com1 como transceiver
#    Env_comando(ser,'interfacemode com1 tcom2 none') 

    
def send_base(ser,comando,check=True):
        # Comando send, funciona pag 190/650
    cabecera='send '+COM_rb+' "'
    comando=cabecera+comando + '"'
    comando=Env_comando(ser,comando,check)
    return comando

def conv_latddmm2d(numero):
    d=math.trunc(numero/100)
    return d+(numero-d*100)/60

def GPSQI(argument):# GPS quality indicator
    # Ver pag 320/650 del manual:
    #        GPS Quality indicator
            #        0 = fix not available or invalid
            #        1 = GPS fix
            #        2 = C/A differential GPS, OmniSTAR HP, OmniSTAR XP, OmniSTAR VBS, or CDGPS
            #        4 = RTK fixed ambiguity solution (RT2), see also Table 90 on page 530
            #        5 = RTK floating ambiguity solution (RT20),OmniSTAR HP or OmniSTAR XP
            #        6 = Dead reckoning mode
            #        7 = Manual input mode (fixed position)
            #        8 = Simulator mode
            #        9 = WAAS    
            tabla={
               0: " fix not available or invalid",
               1: " GPS fix",
               2: " C / A differential GPS, OmniSTAR HP, OmniSTAR XP, OmniSTAR VBS, or CDGPS",
               3: " no hay info de este indicador",
               4: " RTK fixed ambiguity solution (RT2), see also Table 90 on page 530",
               5: " RTK floating ambiguity solution (RT20),OmniSTAR HP or OmniSTAR XP",
               6: " Dead reckoning mode",
               7: " Manual input mode (fixed position)",
               8: " Simulator mode",
               9: " WAAS",                           
                    }
            return tabla.get(argument,"nada")

def resetear(ser,disp):
    Ver_inbuffer(ser) # lee el buffer para limpiarlo.
    if disp=='base': # resetea 
            send_base(ser,'freset command',False)
            print('reseteando base...')
    
    if disp=='rover': # resetea 
            Env_comando(ser,'freset command',False)
            print('reseteando rover...')
            
    t0=time.time()
    t1=t0
    while t1<t0+30:
        banderas=Ver_inbuffer(ser)
        if banderas[1]!=0:
            print('reseteo exitoso de '+ disp)
            return True
         
        t1=time.time()
        
    print('Error: no se puede confirmar el reseteo')
    return False
        
def config_base(ser):
    send_base(ser,'log gpggartk ontime 0.5') # loggea la base para que envie su posicion
    Config_puente(ser)
    print('Esperando estabilizacion... (60segs)')
    k=0
    while k<60:
        k=k+1    
        time.sleep(1)
        Lectura=ser.read_until()
        Lectura=Lectura.split(',')
        if Lectura=="": # por si no hay datos
            Lectura='None'
        
        print('\rquedan: ' + str(60-k) + ' s Lectura actual '+ str(Lectura)),
        sys.stdout.flush()
        
    print('\nComienza la lectura de datos')
    t0=time.time() # tiempo actual
    t1=t0
    N=10
    timeout=100
    Historial=np.zeros((5,N))
    k=-1
    vacio=0
    while t1<t0+timeout and k<N-1:
        time.sleep(0.5)
        t1=time.time()
        if ser.in_waiting>0:
            k=1+k
            Lectura=ser.read_until()
            Lectura=Lectura.split(',')
            print(Lectura)
            if Lectura[6]=='0': # por si no hay datos
                k=k-1
                vacio=vacio+1
                print('Lectura invalida')
            else:
                if k<=(N-1) and Lectura[6]=='1':
                    print('Lectura valida')
                    # Ver pag 320/650 del manual:
                    Historial[0][k]=-conv_latddmm2d(float(Lectura[2])) #lat 
                    Historial[1][k]=-conv_latddmm2d(float(Lectura[4])) #lon 
                    Historial[2][k]=float(Lectura[9]) # altura
                    Historial[3][k]=float(Lectura[7]) # num de satelites
                    Historial[4][k]=float(Lectura[8]) # precision
                else:
                    print('Error: k= '+str(k)+'; GPS Quality indicator='+ GPSQI(float(Lectura[6])))
                    
    if  t1>=t0+timeout:
        print('Error: TimeOut, verificar conexiones')
        print('Reseteando rover y Base...')
        resetear(ser,'rover')
        resetear(ser,'base')
    else:
        # Buscar la mejor lectura
        Lat=st.median(Historial[0,:])
        Long=st.median(Historial[1,:])
        Height=st.median(Historial[2,:])
        print('posicion fijada en: ' + str(Lat) + ' Lat '+str(Long)+' Long '+str(Height)+' altura ')
        print('desvios: '+str(st.stdev(Historial[0,:]))+' std lat '+str(st.stdev(Historial[1,:]))+' std long '+str(st.stdev(Historial[2,:]))+' std Height ')
        # Resetear base y configurarla como rtk con la posicion obtenida anteriormente
        resetear(ser,'rover')
        resetear(ser,'base')
        timer_print(30)
        send_base(ser,'fix position '+str(Lat)+' '+str(Long)+' '+str(Height))
        send_base(ser,'log rtcm3 ontime 10') # base station parameters
        send_base(ser,'log rtcm22 ontime 10 1') # extended base station parameters
        send_base(ser,'log rtcm1819 ontime 1') # raw measurements
        send_base(ser,'log rtcm31 ontime 2') # GLONASS diferential correction
        send_base(ser,'log rtcm32 ontime 2') # GLONASS base station parameters
        send_base(ser,'log rtcm1 ontime 5') # differential GPS correction
        send_base(ser,'interfacemode novatel rtcm on',False)

#        Ver_inbuffer(ser)
        #Lat=-31.5424768
        #Long=-68.5441024
        #Height=640.0

        return
    
# ############################################### Inicio del programa    

if __name__=='__main__':
    while True:
        # Limpio estado anterior
        print('$#####################INICIANDO')
        ser=Config_puerto()
        print('reseteando los sistemas...')
        resetear(ser,'rover')
        resetear(ser,'base')
        timer_print(30)
        config_base(ser)
        Env_comando(ser,'interfacemode '+COM_rb+' rtcm none') # Config RX
        Env_comando(ser,'log gpggartk ontime 0.1') # loggea la base para que envie su posicion
        t0=time.time() # tiempo actual
        t1=t0
        while t1<t0+60*2:
             if ser.in_waiting>0:
                Lectura=ser.read_until()
                Lectura=Lectura.split(',')
                print(Lectura)
                if float(Lectura[6])==4 or float(Lectura[6])==5:
                    print('RTK configurado correctamente; GPS Quality indicator='+ GPSQI(float(Lectura[6])))
                    t0=time.time()# para que no salga del loop
                t1=time.time()
        
        print('$#################### Ocurrio algun error, no se pudo configurar el GPS con RTK, reiniciando...')
              
              
def pirulo2():
        resetear(ser,'base')
        Config_puente(ser)
       
        send_base(ser,'fix position '+str(Lat)+' '+str(Long)+' '+str(Height))
        send_base(ser,'log rtcm3 ontime 10') # base station parameters
        send_base(ser,'log rtcm22 ontime 10 1') # extended base station parameters
        send_base(ser,'log rtcm1819 ontime 1') # raw measurements
        send_base(ser,'log rtcm31 ontime 2') # GLONASS diferential correction
        send_base(ser,'log rtcm32 ontime 2') # GLONASS base station parameters
        send_base(ser,'log rtcm1 ontime 5') # differential GPS correction
        send_base(ser,'interfacemode '+COM_base +' novatel rtcm on',False)
        Ver_inbuffer(ser)
         
         
        send_base(ser,'fix position '+str(Lat)+' '+str(Long)+' '+str(Height))
        send_base(ser,'log '+COM_base +' rtcm3 ontime 10') # base station parameters
        send_base(ser,'log '+COM_base +' rtcm22 ontime 10 1') # extended base station parameters
        send_base(ser,'log '+COM_base +' rtcm1819 ontime 1') # raw measurements
        send_base(ser,'log '+COM_base +' rtcm31 ontime 2') # GLONASS diferential correction
        send_base(ser,'log '+COM_base +' rtcm32 ontime 2') # GLONASS base station parameters
        send_base(ser,'log '+COM_base +' rtcm1 ontime 5') # differential GPS correction
#        send_base(ser,'interfacemode '+COM_base +' none rtcm on',False)
        send_base(ser,'interfacemode '+COM_base +' novatel rtcm on',False)