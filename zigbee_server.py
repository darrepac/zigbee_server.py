#!/usr/bin/env python
import serial
import re
import requests
import sys
import datetime
import traceback
import pdb
import time
import os
import shutil
import urlparse
import eventlet
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer



ser = serial.Serial ('/dev/ttyUSB23', 19200, timeout=1)
print ser.name
line = ""
device = list()
EUI_dongle = ""
eventlet.monkey_patch()

def delai():
	time.sleep(0.2)

def send_order (order):
	global line
	global EUI_dongle
	ser.write(order)
	line = ""
#        print order
        while ("OK" not in line):
		delai()
        	line = ser.readline()
                print line
		if ("Telegesis" in line):
			delai()
	                line = ser.readline()
	                print line
			delai()
	                line = ser.readline()
        	        EUI_dongle = line
                        EUI_dongle = EUI_dongle.replace("\r","")
                        EUI_dongle = EUI_dongle.replace("\n","")
			print line


        line = ""

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Just received a GET request")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        qs = {}
        path = self.path
        tmp = urlparse.urlparse(path).query
        qs = urlparse.parse_qs(tmp)
        print path
	print tmp
        print str(qs)
	if qs.has_key('INIT'):
		send_order("ATI\r")
		send_order("AT+PANSCAN\r")

	elif qs.has_key('JOIN'):
		send_order("ATI\r")
		send_order("AT+JN\r")
		send_order("AT+N\r")

        elif qs.has_key('NETINFO'):
                send_order("ATI\r")
                send_order("AT+N\r")

	elif qs.has_key('DISCOVER'):
		send_order("ATI\r")
		file = open('/home/pi/scripts/zigbee_devices.txt', 'w')
		nbr_device = qs.get('DISCOVER')[0]
		next = 1
		index = 0
		ident = "FF"
		index_ident = 0
		while (len(list(set(device))) < int(nbr_device)):
			while (next == 1):
				ser.write("AT+NTABLE:0" + str(index) + "," + ident + "\r")
				time.sleep (1)
				cont = 0
				next = 0
				sousindex = 0
				while ("ACK" not in line):
                			line = ser.readline()
					time.sleep(1)
        	        		print line
					if (cont == 1 and "|" in line and "RFD" not in line and EUI_dongle not in line):
#						device_total = index+sousindex
#						print "device"+str(device_total)+" Cont"+str(cont)+" Next"+str(next)
						ID = line.split(' | ')[3]
						print ID
						device.append(ID)
						sousindex += 1

					if ("EUI" in line):
						cont = 1
					if ("2." in line or "5." in line or "8." in line):
						next = 1
						print "detection 2 5 8"
				
	        		line = ""
				index += 3
#			pdb.set_trace()
			print "Changement de device: " + str(index_ident)
			ident = device[index_ident]
			index_ident += 1
			next = 1
			index = 0
		for i in list(set(device)):
			print i
			file.write(i + "\n")
		file.close

	elif qs.has_key('ENDPOINT'):
		send_order("ATI\r")
		oldfile = open('/home/pi/scripts/zigbee_devices.txt', 'r+')
		newfile = open('/home/pi/scripts/temp.txt', 'w')
#		pdb.set_trace()
		for ligne in oldfile:
			ligne = ligne.replace("\r","")
                        ligne = ligne.replace("\n","")
#			print "AT+ACTEPDESC:" + ligne + "," + ligne + "\r"
			ser.write("AT+ACTEPDESC:" + ligne + "," + ligne + "\r")
#                        ser.flush()
			time.sleep(1)
			while ("ACK" not in line):
                                line = ser.readline()
                                print line
				time.sleep(1)
				if ("ActEpDesc" in line):
					EP = line.split(',')[2]
					EP = EP.replace("\r","")
		                        EP = EP.replace("\n","")
					newfile.write(ligne.replace(ligne,ligne+ "|" + EP + "\n")) 
			line =""
		oldfile.close
		newfile.close
		os.remove('/home/pi/scripts/zigbee_devices.txt')
		shutil.move('/home/pi/scripts/temp.txt','/home/pi/scripts/zigbee_devices.txt')
	
	elif qs.has_key('IDENTIFY'):
                send_order("ATI\r")
                oldfile = open('/home/pi/scripts/zigbee_devices.txt', 'r+')
                newfile = open('/home/pi/scripts/temp.txt', 'w')
                for ligne in oldfile:
                        ligne = ligne.replace("\r","")
                        ligne = ligne.replace("\n","")
			input_var = raw_input("delai() d'attente pour volet " + ligne.split('|')[0] + " en secondes? ")
                        time.sleep(int(input_var))
                        ser.write("AT+IDENTIFY:" + ligne.split('|')[0] + "," + ligne.split('|')[1] + ",0,000A\r")
                        time.sleep(1)
                        while ("OK" not in line):
                                line = ser.readline()
                                print line
                                time.sleep(1)
			input_var = raw_input("Nom pour ce volet: ")
                        newfile.write(ligne.replace(ligne,ligne+ "|" + input_var + "\n"))
			line =""
                oldfile.close
                newfile.close

	elif qs.has_key('MONTER'):
		if qs.get('MONTER')[0] != "ALL":
#			only one
			device_text = qs.get('MONTER')[0]
			with open('/home/pi/scripts/zigbee_devices.txt') as devices:
				for line in devices:
					line = line.rstrip()
					if (device_text == line.split('|')[2]):
#						ser.write("AT+RONOFF:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,1\r")
						ser.write("AT+LCMV:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,1,00,FF\r")
                                                receive = ""
						delai()
                                                while ("DFTREP" not in receive):
                                                        receive = ser.readline()
                                                        print receive
                                                        delai()
                                                receive = receive.rstrip()
                                                if (receive.split(',')[4] != "00"):
#                                                       print receive.split(',')[4]
                                                        print "Transmit KO to " + line.split('|')[2] + "\n"
                                                else:
                                                        print "Transmit OK to " + line.split('|')[2] + "\n"

		else:
#			all
			with open('/home/pi/scripts/zigbee_devices.txt') as devices:
                                for line in devices:
                                        line = line.rstrip()
#                                        ser.write("AT+RONOFF:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,1\r")
					ser.write("AT+LCMV:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,1,00,FF\r")
                                        receive = ""
					delai()
                                        while ("DFTREP" not in receive):
                                        	receive = ser.readline()
                                                print receive
                                                delai()
                                        receive = receive.rstrip()
                                        if (receive.split(',')[4] != "00"):
#                                       	print receive.split(',')[4]
                                                print "Transmit KO to " + line.split('|')[2] + "\n"
                                        else:
                                                print "Transmit OK to " + line.split('|')[2] + "\n"

	elif qs.has_key('DESCENDRE'):
		print "Commande descendre recu"
                if qs.get('DESCENDRE')[0] != "ALL":
#                       only one
                        device_text = qs.get('DESCENDRE')[0]
                        with open('/home/pi/scripts/zigbee_devices.txt') as devices:
                                for line in devices:
                                        line = line.rstrip()
                                        if (device_text == line.split('|')[2]):
#						ser.write("AT+RONOFF:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,0\r")
						ser.write("AT+LCMV:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,1,01,FF\r")
						receive = ""
						delai()
	                                        while ("DFTREP" not in receive):
        	                                        receive = ser.readline()
                	                                print receive
                        	                        delai()
                                	        receive = receive.rstrip()
                                        	if (receive.split(',')[4] != "00"):
#                                               	print receive.split(',')[4]
                                                	print "Transmit KO to " + line.split('|')[2] + "\n"
                                        	else:
                                                	print "Transmit OK to " + line.split('|')[2] + "\n"

                else:
#                       all
                        with open('/home/pi/scripts/zigbee_devices.txt') as devices:
                                for line in devices:
                                        line = line.rstrip()
#                                        ser.write("AT+RONOFF:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,0\r")
					ser.write("AT+LCMV:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,1,01,FF\r")
                                        receive = ""
					delai()
                                        while ("DFTREP" not in receive):
                                                receive = ser.readline()
                                                print receive
                                                delai()
                                        receive = receive.rstrip()
                                        if (receive.split(',')[4] != "00"):
#                                               print receive.split(',')[4]
                                                print "Transmit KO to " + line.split('|')[2] + "\n"
                                        else:
                                                print "Transmit OK to " + line.split('|')[2] + "\n"


        elif qs.has_key('MOVETO'):
                if qs.get('MOVETO')[0] != "ALL":
#                       only one
			level = int(qs.get('LEVEL')[0])
			a = -0.0084
			b = 3.04
			c = 35 
			level = level * level * a + level * b + c 
			level = int(level)
			level = format(level,'02X')
                        device_text = qs.get('MOVETO')[0]
                        with open('/home/pi/scripts/zigbee_devices.txt') as devices:
                                for line in devices:
                                        line = line.rstrip()
                                        if (device_text == line.split('|')[2]):
                                                ser.write("AT+LCMVTOLEV:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,0," + level + ",000F\r")
                                                receive = ""
                                                delai()
						while ("DFTREP" not in receive):
                                                        receive = ser.readline()
                                                        print receive
                                                        delai()
                                                receive = receive.rstrip()
                                                if (receive.split(',')[4] != "00"):
#                                                       print receive.split(',')[4]
                                                        print "Transmit KO to " + line.split('|')[2] + "\n"
                                                else:
                                                        print "Transmit OK to " + line.split('|')[2] + "\n"

                else:
#                       all
			level = int(qs.get('LEVEL')[0])
                        a = -0.0084
                        b = 3.04
                        c = 35
                        level = level * level * a + level * b + c
                        level = int(level)
                        level = format(level,'02X')

                        with open('/home/pi/scripts/zigbee_devices.txt') as devices:
                                for line in devices:
                                        line = line.rstrip()
					ser.write("AT+LCMVTOLEV:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,0," + level + ",000F\r")                        
                                        receive = ""
                                        while ("DFTREP" not in receive):
                                                receive = ser.readline()
                                                print receive
                                                delai()
                                        receive = receive.rstrip()
                                        if (receive.split(',')[4] != "00"):
#                                               print receive.split(',')[4]
                                                print "Transmit KO to " + line.split('|')[2] + "\n"
                                        else:
                                                print "Transmit OK to " + line.split('|')[2] + "\n"






	elif qs.has_key('STATUS'):
		a=0.00081872
		b=0.2171167
		c=-8.60201639
		if qs.get('STATUS')[0] == "ALL":
#all
                        with open('/home/pi/scripts/zigbee_devices.txt') as devices:
                                for line in devices:
                                        with eventlet.Timeout(10, False):
						line = line.rstrip()
                                                delai()
						print line
                                                ser.write("AT+READATR:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,0008,0000\r")
                                                receive=""
                                                print "1 " + line.split('|')[2]
                                                while ("OK" not in receive):
                                                        receive = ser.readline()
                                                        print receive
                                                        delai()


						while (("RESPATTR" and line.split('|')[0]) not in receive):
                                                        receive = ser.readline()
                                                        print receive
                                                        delai()
                                                print "2 " + receive
                                                receive = receive.rstrip()
                                                level = int(receive.split(',')[5],16)
                                                print level
                                                level = int(level * level * a + level * b + c)
                                                if level < 0 :
                                                        level = 0
                                                print line.split('|')[2] + " est au niveau " + str(level) + " \n"
                                                level = int(level * 32 / 100)

						if level == 0:
							request = "http://192.168.0.19:9090/json.htm?type=command&param=udevice&idx=" + line.split('|')[3] + "&nvalue=1"
                	                        elif level > 31:
							request = "http://192.168.0.19:9090/json.htm?type=command&param=udevice&idx=" + line.split('|')[3] + "&nvalue=0"
						else:
							request = "http://192.168.0.19:9090/json.htm?type=command&param=udevice&idx=" + line.split('|')[3] + "&nvalue=16&svalue=" + str(level)
						print request
						r = requests.get(request)
						print "Suivant\n"
		else:
#one -> not done
			print "Un seul Status\n"
			device_text = qs.get('STATUS')[0]
               		with open('/home/pi/scripts/zigbee_devices.txt') as devices:
                                for line in devices:
                                        line = line.rstrip()
					if (device_text == line.split('|')[2]):
	                                        ser.write("AT+READATR:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,0006,0000\r")
                	                        receive = ""
                        	                while ("RESPATTR" not in receive):
                                	                receive = ser.readline()
                                     	        	print receive
	                                                delai()
        	                                receive = receive.rstrip()
                	                        if (receive.split(',')[5] != "00"):
#                       	                        print receive.split(',')[4]
                                	                print line.split('|')[2] + " est ouvert. Niveau: "
						else:
							print line.split('|')[2] + " est ferme. Niveau: "
                                       	        ser.write("AT+READATR:" + line.split('|')[0] + "," + line.split('|')[1] + ",0,0008,0000\r")
       	                                        receive=""
               	                                delai()
                       	                        while ("RESPATTR" not in receive):
                               	                        receive = ser.readline()
                                      	                print receive
                                               	        delai()
                                                receive = receive.rstrip()
       	                                        level = int(receive.split(',')[5],16)
               	                                level = int(level * level * a + level * b + c)
						print str(level) + " \n"
						if level < 0 :
							level = 0
						level = int(level * 32 / 100)
						level = 32 - level




	elif qs.has_key('DIRECT'):
		send_order("ATI\r")
	        ser.write(qs.get('DIRECT')[0] + "\r")
		time.sleep (1)
        	while (1):
                	line = ser.readline()
                	print line
			



        return


if __name__ == "__main__":
    try:
        server = HTTPServer(('192.168.0.19', 1234), MyHandler)
        print('Started http server')
        server.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down server')
        server.socket.close()
	ser.close()
	sys.exit()
