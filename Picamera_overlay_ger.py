#!/usr/bin/python
# -*- coding: utf-8 -*-
#Adrian Mayer, Swarovskioptik Absam
#14.11.2016

import time
import picamera
import sys
import os
from PIL import Image, ImageDraw
import curses
from math import fabs,pow,sqrt,atan,degrees
import subprocess


#######################################################
#EINSTELLUNGEN ANFANG
#######################################################

##Bild
stream_width = 1920         #Auflösung in X
stream_height = 1080        #Auflösung in Y
stream_fps = 90             #Maximale Bilder pro Sekunde (siehe Kamera Datenblatt für kompartible fps)
stream_hflip = True         #Spiegelt das Bild in der Vertikale (True/False)
stream_vflip = False        #Spiegelt das Bild in der Horizontale (True/False)
stream_sharpness = 100      #Schärfe des Bildes (-100 bis 100) , Standart = 0
stream_saturation = 0       #Sättigung des Bildes (-100 bis 100) , Standart = 0


##Pixel pro Messeinheit
pixelper_unit = 0           #Gibt an wieviele Pixel einer Messeinheit entsprechen. Wenn nicht vorhanden = 0 setzen!

##Overlay(Werte 0-255)
overlay_alpha = 128         #Gibt die Transparenz des Overlays an. 255= Undurchsichtig, 0 = Transparent

##Fadenkreuz
crosshair_length = 125      #Strichlänge des Fadenkreuzes
crosshair_offset = 3        #Offset der Fadenkreuzstriche zum Fadenkreuz Zentrum
crosshair_thickness = 1     #Strichdicke des Fadenkreuzes

##Fadenkreuz Ursprung (Standart = Bildschirmmitte)
crosshair_offset_x=0        #Bestimmt den horizontalen Offset des Ursprunges (ausgehend von der Bildschirmmitte)
crosshair_offset_y=0        #Bestimmt den vertikalen Offet des Ursprunges (ausgehend von der Bildschirmmitte)

###Fadenkreuz Farbe (Werte 0-255)
crosshair_color_red= 255    #Rotanteil der Fadenkreuzfarbe
crosshair_color_green= 0    #Grünanteil der Fadenkreuzfarbe
crosshair_color_blue= 0     #Blauanteil der Fadenkreuzfarbe

##Toleranzbereich
tolerance_size_x = 61       #Größe des Tolerenzbereiches in x Achse (Pixel)
tolerance_size_y = 31       #Größe des Toleranzbereiches in y Achse (Pixel)

###Toleranzbereich Farbe (Werte 0-255)
tolerance_color_red= 0      #Rotanteil des Toleranzbereiches
tolerance_color_green = 255 #Grünanteil des Toleranzbereiches
tolerance_color_blue = 0    #Blauanteil des Toleranzbereiches

#Kamermaname
camera_name = "Cam 1"       #Optionaler Name der Kamera


#######################################################
#EINSTELLUNGEN ENDE
#######################################################

#Globals

cr_l = crosshair_length
cr_o = crosshair_offset
cr_t = crosshair_thickness
cr_c = (crosshair_color_red , crosshair_color_green, crosshair_color_blue)

tl_s_x = tolerance_size_x
tl_s_y = tolerance_size_y
tl_c = (tolerance_color_red,tolerance_color_green,tolerance_color_blue)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    LIGHTGREEN = '\033[32m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WHITE = '\033[37m'
    LIGHTBLUE = '\033[34m'
    WEAKBLUE = '\033[94m'
    

def msg_positive(msg):
    print(bcolors.BOLD + "[" + bcolors.OKGREEN + "+" + bcolors.WHITE + "] "+ bcolors.ENDC + str(msg))
    return
def msg_neutral(msg):
    print(bcolors.BOLD + "[" + bcolors.LIGHTBLUE + "I" + bcolors.WHITE + "] "+ bcolors.ENDC + str(msg))    
    return
def msg_warning(msg):
    print(bcolors.BOLD + "[" + bcolors.WARNING + "!" + bcolors.WHITE + "] " + bcolors.ENDC + bcolors.WARNING + str(msg) + bcolors.ENDC) 
    return
def msg_error(msg):
    print(bcolors.BOLD + "[" + bcolors.FAIL + "X" + bcolors.WHITE + "] "+ bcolors.ENDC + bcolors.FAIL + str(msg) + bcolors.ENDC) 
    return
def msg_input(msg):
    print(bcolors.BOLD + "[" + bcolors.OKBLUE + "?" + bcolors.WHITE + "] " + bcolors.ENDC + bcolors.OKBLUE + str(msg) + bcolors.ENDC)
    return input()

def msg_count(alist,msg):
    print(bcolors.BOLD + "[" + bcolors.LIGHTGREEN + "*" + bcolors.WHITE + "] " + bcolors.ENDC + bcolors.LIGHTGREEN + str(msg) + bcolors.ENDC)
    for item in alist:
        print(bcolors.BOLD + "   [" + bcolors.LIGHTGREEN + str(alist.index(item)) + bcolors.WHITE + "] " + bcolors.ENDC + bcolors.LIGHTGREEN + str(item) + bcolors.ENDC)
        

"""Chattest
msg_positive("Dies ist positiv")
msg_neutral("Dies ist neutral")
msg_warning("Dies ist eine warnung")
msg_error("Dies ist ein Fehler")
input('input something!: ')"""

#######################################################
#Unterprogramme ANFANG
#######################################################   
def intro():
    print(bcolors.WHITE + bcolors.BOLD)
    print("\n____ ___     ____ _  _ ____ ____ _    ____ _   _ ")
    print("|__/ |__]    |  | |  | |___ |__/ |    |__|  \_/  ")
    print("|  \ |       |__|  \/  |___ |  \ |___ |  |   |   ")
    print("-------------------------------------------------")
    print("   Swarovski Optik Absam, Raspberry Pi Overlay   ")
    print("        V1.00, Adrian Mayer , 17.11.2016         ")
    print("-------------------------------------------------")
    print(bcolors.ENDC)
    return

def search_overlayimg():
    rootpath = "/media/pi/"
    folders = os.listdir(rootpath)
    folders.remove("SETTINGS")
    if len(folders) < 1:
        msg_neutral("Keine USBs erkannt")
        return
    msg_count(folders,"Liste der erkannten USBs: ")
    msg_neutral("Überprüfe USBs auf Overlay Bilder...")
    overlays=[]
    for usb in folders:
        if (os.path.isfile(rootpath+usb+"/overlay.png")):
            overlays.append(rootpath+usb+"/overlay.png")
        else:
            msg_warning("Es konnte kein overlay.png gefunden in " +usb+ " werden")
            return
    if(len(overlays) <=1):
        return overlays[0]
    msg_count(overlays,"Liste der verfügbaren Overlay Bilder:")
    selected = False
    while (selected == False):
        ans =msg_input("Verwende Overlay Nr: ")
        try:
            tmp = overlays[int(ans)]
            return tmp
        except:
            msg_error("Ungültige Eingabe!")
            continue
    return ""

def screenshot ():
    file = open('testscreenshot.jpg' , 'wb')
    camera.capture(file)
    file.close()

def isinrange(checkvar):
    """ checks if int is out of byte range """
    return checkvar >= 0 and checkvar <= 255

def getscreenreso():
    cmd = ['xrandr']
    cmd2 = ['grep', '*']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE)
    p.stdout.close()
     
    resolution_string, junk = p2.communicate()
    resolution = str(resolution_string.split()[0])
    resolution = [ str(resolution.split("x")[0].split("'")[1]), str(resolution.split("x")[1].split("'")[0]) ]
    return int(resolution[0]),int(resolution[1])

def draw_mask(offset_x,offset_y,options,messure=False,lineal=False):
    #Berechnung des Offsets
    cr_w = stream_width/2 + offset_x
    cr_h = stream_height/2 + offset_y
    #Erstellen der Maske
    im = Image.new('RGB', (stream_width, stream_height), (0, 0, 0)) 
    draw = ImageDraw.Draw(im)

    global pixelper_unit

    ##Zeichnen des Toleranzbereiches
    if (options=="ellipse_filled"):
        draw.ellipse((cr_w-(tl_s_x/2), cr_h-(tl_s_y/2), cr_w + (tl_s_x/2),cr_h + (tl_s_y/2)), outline=tl_c, fill=tl_c)
    if (options=="ellipse_filled_q"):
        draw.ellipse((cr_w-(tl_s_x/2), cr_h-(tl_s_x/2), cr_w + (tl_s_x/2),cr_h + (tl_s_x/2)), outline=tl_c, fill=tl_c)
    if (options=="ellipse_outline"):
        draw.ellipse((cr_w-(tl_s_x/2), cr_h-(tl_s_y/2), cr_w + (tl_s_x/2),cr_h + (tl_s_y/2)), outline=tl_c)
    if (options=="ellipse_outline_q"):
        draw.ellipse((cr_w-(tl_s_x/2), cr_h-(tl_s_x/2), cr_w + (tl_s_x/2),cr_h + (tl_s_x/2)), outline=tl_c)    
    if (options=="rectangle_outline"):
        draw.rectangle((cr_w-(tl_s_x/2), cr_h-(tl_s_y/2), cr_w + (tl_s_x/2),cr_h + (tl_s_y/2)), outline=tl_c)
    if (options=="rectangle_outline_q"):
        draw.rectangle((cr_w-(tl_s_x/2), cr_h-(tl_s_x/2), cr_w + (tl_s_x/2),cr_h + (tl_s_x/2)), outline=tl_c)
    if (options=="rectangle_filled"):
        draw.rectangle((cr_w-(tl_s_x/2), cr_h-(tl_s_y/2), cr_w + (tl_s_x/2),cr_h + (tl_s_y/2)), outline=tl_c , fill=tl_c)
    if (options=="rectangle_filled_q"):
        draw.rectangle((cr_w-(tl_s_x/2), cr_h-(tl_s_x/2), cr_w + (tl_s_x/2),cr_h + (tl_s_x/2)), outline=tl_c , fill=tl_c)
    if (options=="unitgrid" and pixelper_unit != 0):
        ticks_x = stream_width / int(pixelper_unit) /2
        ticks_y = stream_height / int(pixelper_unit) /2
        for x in range (0,ticks_x+1):
            draw.line((cr_w+(x*pixelper_unit),0,cr_w+(x*pixelper_unit),stream_height), fill=(64,64,64))
        for x in range (0,ticks_x+1):
            draw.line((cr_w-(x*pixelper_unit),0,cr_w-(x*pixelper_unit),stream_height), fill=(64,64,64))
        for x in range (0,ticks_y+1):
            draw.line((0,cr_h-(x*pixelper_unit),stream_width,cr_h-(x*pixelper_unit)), fill=(64,64,64))
        for x in range (0,ticks_y+1):
            draw.line((0,cr_h+(x*pixelper_unit),stream_width,cr_h+(x*pixelper_unit)), fill=(64,64,64))
            
    ##Zeichnen des Fadenkreuzes
    draw.line((cr_w - cr_o, cr_h, cr_w - (cr_o + cr_l),cr_h), fill= cr_c, width= cr_t)
    draw.line((cr_w + cr_o, cr_h, cr_w + (cr_o + cr_l),cr_h), fill= cr_c, width= cr_t)
    draw.line((cr_w, cr_h + cr_o, cr_w,cr_h + (cr_o + cr_l)), fill= cr_c, width= cr_t)
    draw.line((cr_w, cr_h - cr_o, cr_w,cr_h - (cr_o + cr_l)), fill= cr_c, width= cr_t)
    
    ##Zeichnen des Messure Lineales
    if setup_measure:
        draw.line((cr_w + ui_ms_offset_x, 0 , cr_w + ui_ms_offset_x,stream_height),fill = (0,0,255),width = 1)
        draw.line((0, cr_h + ui_ms_offset_y , stream_width,cr_h + ui_ms_offset_y),fill = (0,0,255),width = 1)
        pixelper_unit = fabs(ui_ms_offset_x)

    ##Zeichnen/Berechnung des Lineales
    if not setup_measure and lineal:
        lineal_units_x = fabs(ui_li_offset_x) / pixelper_unit
        lineal_units_y = fabs(ui_li_offset_y) / pixelper_unit
        lineal_units_c = sqrt(pow(fabs(ui_li_offset_y),2) + pow(fabs(ui_li_offset_x),2)) / pixelper_unit
        angle = 0

        if ui_li_offset_x > 0 and ui_li_offset_y > 0: #4 quadrant
            angle = 360 - degrees(atan(float(ui_li_offset_y)/float(ui_li_offset_x)))
        if ui_li_offset_x < 0 and ui_li_offset_y > 0: #3
            angle = 180 -degrees(atan(float(ui_li_offset_y)/float(ui_li_offset_x)))
        if ui_li_offset_x < 0 and ui_li_offset_y < 0: #2
            angle = 180 -degrees(atan(float(ui_li_offset_y)/float(ui_li_offset_x)))
        if ui_li_offset_x > 0 and ui_li_offset_y < 0: #1
            angle = -degrees(atan(float(ui_li_offset_y)/float(ui_li_offset_x)))

        if ui_li_offset_x == 0 and ui_li_offset_y > 0:
            angle = 270
        if ui_li_offset_x < 0 and ui_li_offset_y == 0:
            angle = 180
        if ui_li_offset_x == 0 and ui_li_offset_y < 0:
            angle = 90

        draw.pieslice((cr_w-20,cr_h-20,cr_w+20,cr_h+20),-int(angle),0,outline=(0,0,255) , fill = (0,0,255))
        
        draw.line((cr_w + ui_li_offset_x, 0 , cr_w + ui_li_offset_x,stream_height),fill = (255,255,255),width = 1)
        draw.line((0, cr_h + ui_li_offset_y , stream_width, cr_h + ui_li_offset_y),fill = (255,255,255),width = 1)
        draw.line((cr_w,cr_h,cr_w+ui_li_offset_x,cr_h+ui_li_offset_y), fill = (64,64,64), width = 1)
        

    ##Print der Info
    if not setup_measure:    
        if setup_locked:
            draw.text((10,10),"Setup GESPERRT")
        else:
            draw.text((10,10),"Setup ENTSPERRT, 'S' zweimal druecken zum Sperren")
            draw.text((10,20),"Fadenkreuz Offset X:" + str(ui_cr_offset_x)+ " (Pfeiltasten)")
            draw.text((10,30),"Fadenkreuz Offset Y:" + str(ui_cr_offset_y*-1) + " (Pfeiltasten)")
            draw.text((10,40),"Fadenkreuz Zentrum Offset: " + str(cr_o) + " ('+'/'-')")
            draw.text((10,50),"Toleranz Typ: " + options + " (1-9)")
            draw.text((10,60),"Overlay Transparenz: " + str(overlay_alpha) + " (','/';')")
            if lineal:
                draw.text((10,70),"Pixel pro Einheit: " + str(pixelper_unit))
                draw.text((10,80),"Lineal Messung delta: X= " + str(lineal_units_x) + " Y= " + str(lineal_units_y))
                draw.text((10,90),"Lineal Messung delta: Betrag= " + str(lineal_units_c))
                draw.text((10,100),"Winkel: " + str(angle))

                draw.text((cr_w + ui_li_offset_x+10, cr_h + ui_li_offset_y+10),"dX= " + str(round(lineal_units_x,3))+ " dY= " + str(round(lineal_units_y,3)))
                draw.text((cr_w + ui_li_offset_x/2-10, cr_h + ui_li_offset_y/2-5),"Betrag= " + str(round(lineal_units_c,3)))
                draw.text((cr_w + ui_li_offset_x/2-10, cr_h + ui_li_offset_y/2+5),"Winkel= " + str(round(angle,3)))
    else:
        if setup_locked:
            draw.text((10,10),"Setup GESPERRT")
        else:
            draw.text((10,10),"Setup ENTSPERRT, 'S' zweimal druecken zum Sperren")
            draw.text((10,20),"Verschieben Sie den Cursor mittels Pfeiltasten")
            draw.text((10,30),"und erfassen Sie eine Messeinheit")
            draw.text((10,40),"Schließen Sie die Messung mit 'm' ab")
            draw.text((10,50),"Eine Einheit entspricht: " +  str(pixelper_unit) + " Pixel") 
    return im

def checksetup():
    #Überprüfung des Setups
    isvalid = True
    width,height = getscreenreso()
    err = "Überprüfen Sie die/den Parameter: "

    if not isinrange(overlay_alpha):
        isvalid = False
        err += "\noverlay_alpha; Der Wert liegt außerhalb des Byte Wertebereichs (0-255)"

    if not isinrange(crosshair_color_red):
        isvalid = False
        err += "\ncrosshair_color_red; Der Wert liegt außerhalb des Byte Wertebereichs (0-255)"

    if not isinrange(crosshair_color_green):
        isvalid = False
        err += "\ncrosshair_color_green; Der Wert liegt außerhalb des Byte Wertebereichs (0-255)"

    if not isinrange(crosshair_color_blue):
        isvalid = False
        err += "\ncrosshair_color_blue; Der Wert liegt außerhalb des Byte Wertebereichs (0-255)"

    if not isinrange(tolerance_color_red):
        isvalid = False
        err += "\ntolerance_color_red; Der Wert liegt außerhalb des Byte Wertebereichs (0-255)"

    if not isinrange(tolerance_color_green):
        isvalid = False
        err += "\ntolerance_color_green; Der Wert liegt außerhalb des Byte Wertebereichs (0-255)"

    if not isinrange(tolerance_color_blue):
        isvalid = False
        err += "\ntolerance_color_blue; Der Wert liegt außerhalb des Byte Wertebereichs (0-255)"

    if (stream_width <= 0):
        isvalid = False
        err += "\nstream_width; Die Breite des Streams darf nicht < 0 sein!"

    if (stream_height <= 0):
        isvalid = False
        err += "\nstream_height; Die Höhe des Streams darf nicht < 0 sein!"

    if (crosshair_length <= crosshair_offset):
        isvalid = False
        err += "\ncrosshair_length/crosshair_offset; Die Länge der Fadenkreuzes darf nicht kleiner als der Offset sein, "

    if (crosshair_thickness % 2 !=1):
        isvalid = False
        err += "\ncrosshair_thickness; Bei Wahl einer geraden Strichgöße ist das Fadenkreuz nicht zentriert!"

    if (tolerance_size_x % 2 !=1):
        isvalid = False
        err += "\ntolerance_size; Bei Wahl eines geraden Toleranzwertes ist dieser nicht zentriert!"

    if (tolerance_size_y % 2 !=1):
        isvalid = False
        err += "\ntolerance_size; Bei Wahl eines geraden Toleranzwertes ist dieser nicht zentriert!"

    if not isvalid:
        msg_error("Unzulässige Einstellungen vorhanden!\n" + err)
        input("")
        sys.exit()

    if (stream_width > width or stream_height > height):
        msg_warning("Warnung: stream_width/stream_height; Die gewählte Stream Auflösung " + str(stream_width) + "X" + str(stream_height) + " ist größer als die gegebene Monitor Auflösung! ("+str(width)+"x"+str(height)+")")

    if (overlay_alpha >= 230):
        msg_warning("Warnung: Overlay_alpha > 230. Durch einen zu hohen Alphawert wird das eigentliche Kamerabild kaum sichtbar!")

    if (overlay_alpha <= 30):
        msg_warning("Warnung: Overlay_alpha < 30. Durch einen zu niedrigen Alphawert wird das eigentliche Overlay kaum sichtbar!")
    return

def draw_add_info(mask):
    return
        
def stream_start(mask):
    #Starten des Streams
    camera.resolution = (stream_width, stream_height)
    camera.framerate = stream_fps
    camera.saturation = int(stream_saturation)
    camera.sharpness= int(stream_sharpness)
    camera.start_preview()
    camera_preview_fullscreen = True
    camera.hflip=stream_hflip
    camera.vflip=stream_vflip
    #Zeichnen der Beschriftung
    if (camera_name != ""):
        camera.annotate_text = camera_name
    o = camera.add_overlay(mask.tostring(), size=mask.size, layer=3, alpha=overlay_alpha)
    return o

def stream_alphachange(mask,messure,lineal):
    source = draw_mask(crosshair_offset_x + ui_cr_offset_x,crosshair_offset_y + ui_cr_offset_y,tolerancetype,messure,lineal)
    camera.remove_overlay(mask)
    return camera.add_overlay(source.tostring(), size=source.size, layer=3 , alpha= overlay_alpha)

def stream_changeoverlay(newmask):
    camera.remove_overlay(usedoverlay)
    return camera.add_overlay(newmask.tostring(), size=newmask.size, layer=3, alpha=overlay_alpha)

def stream_hideoverlay(newmask):
    camera.remove_overlay(usedoverlay)
    return camera.add_overlay(newmask.tostring(), size=newmask.size, layer=1, alpha=overlay_alpha)

def stream_update_hard(messure= False,lineal= False):
    usedoverlay = stream_changeoverlay(draw_mask(crosshair_offset_x + ui_cr_offset_x,crosshair_offset_y + ui_cr_offset_y,tolerancetype,messure,lineal))
    return usedoverlay


def stream_update(messure= False,lineal= False):
    try:
        im = draw_mask(crosshair_offset_x + ui_cr_offset_x,crosshair_offset_y + ui_cr_offset_y,tolerancetype,messure,lineal)
        usedoverlay.update(im.tostring())
        return usedoverlay
    except:
        return usedoverlay



def movement_incrementer(step,repeats,key):
    global input_key
    global input_repeats
    global movement_smallstep
    if key != input_key:
        curses.flushinp()
        input_key = key
        input_repeats = 0
        movement_smallstep = 1
    if (input_repeats >= repeats):
        movement_smallstep+=1
    input_repeats+=1

    if repeats > 100:
        curses.flushinp()
    return movement_smallstep
        

#######################################################
#Unterprogramme ENDE
#######################################################

#Globals
ui_cr_offset_x = 0
ui_cr_offset_y = 0
ui_ms_offset_x = 0
ui_ms_offset_y = 0
ui_li_offset_x = 0
ui_li_offset_y = 0
pixelper_unit = 1
tolerancetype= "ellipse_filled_q"
setup_locked = True
setup_measure = False
setup_lineal = False
input_key = ord('_')
input_repeats = 0
movement_smallstep = 1
imgoverlay = ""
useimg= False
nooverlay = False


#Start nach Config
intro()
msg_positive("Setup erfolgreich geladen")
msg_neutral("Startparameter werden überprüft")
try:
    checksetup()
    msg_positive("Setupparameter OK")
except:
    e = sys.exc_info()[0]
    msg_error("Schwerwiegender Fehler im Setup.\nSetup nicht vollständig?\n" +str(e))
msg_neutral("Suche nach Overlay Image. 'overlay.png'")
try:
    imgoverlay = search_overlayimg()
except:
    msg_error("Fehler beim suchen nach dem Overlay Image")
msg_positive("Verwendetes Overlay: " + str(imgoverlay))
msg_neutral("Kamera wird initialisiert")
try:
    camera = picamera.PiCamera()
    msg_positive("Kamera erfolgreich initialisiert: Auflösung:" + str(stream_width) +"x"+ str(stream_height) + " MaxFps:" + str(stream_fps))
except:
    msg_error("Kamera konnte nicht initialisiert werden!\nKamera nicht verbunden?")
    
msg_neutral("Erstellen des Overlays " + str(stream_width) + "x" + str(stream_height))
try :
    mask = draw_mask(crosshair_offset_x,crosshair_offset_y,tolerancetype)
    msg_positive("Overlay erfolgreich erstellt")
except:
    msg_error("Fehler beim Erstellen des Overlays.\nVariablen außerhalb des Einstellungsbereichs editiert?")
input("Overlay bereit. Enter Taste zum Starten druecken")
usedoverlay = stream_start(mask)
msg_neutral("Warten auf User Input")

#Input Idle

safetykey = 0
stdscr = curses.initscr()
#curses.noecho()
curses.cbreak()
stdscr.keypad(1)

try:
    while 1:
        c = stdscr.getch()
        
        if c == ord('q'):
            msg_neutral("Schließe Raspberry Pi Camera Overlay")
            break
        
        if c == ord('s'):
            if safetykey >= 1:
                setup_locked = not setup_locked
                usedoverlay = stream_update(setup_measure,setup_lineal)
                safetykey = 0
            else:
                safetykey += 1

        if c== ord('n'):
            im = Image.open(imgoverlay)
            camera.remove_overlay(usedoverlay)
            usedoverlay = camera.add_overlay(im.tostring(), size=im.size, layer=3, alpha=255)
            
        if c== ord('v') and imgoverlay != "":
            useimg = not useimg
            if(useimg):
                im = Image.open(imgoverlay)
                camera.remove_overlay(usedoverlay)
                usedoverlay = camera.add_overlay(im.tostring(), size=im.size, layer=3, alpha=overlay_alpha)
            else:
                usedoverlay = stream_update_hard(setup_measure,setup_lineal)
        if c == ord('b'):
            screenshot()
            
        if not setup_locked: 
        
            #Toleranz Typ
            if c == ord('0'):
                tolerancetype="none"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('1'):
                tolerancetype="ellipse_filled"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('2'):
                tolerancetype="ellipse_filled_q"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('3'):
                tolerancetype="ellipse_outline"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('4'):
                tolerancetype="ellipse_outline_q"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('5'):
                tolerancetype="rectangle_filled"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('6'):
                tolerancetype="rectangle_filled_q"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('7'):
                tolerancetype="rectangle_outline"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('8'):
                tolerancetype="rectangle_outline_q"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('9'):
                tolerancetype="unitgrid"
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == 263:
                nooverlay = not nooverlay
                if nooverlay:                   
                    tolerancetype="none"
                    usedoverlay = stream_hideoverlay(Image.new('RGB', (stream_width, stream_height), (0, 0, 0)))
                else:
                    usedoverlay = stream_update_hard(setup_measure,setup_lineal)
                continue

            #Messurement mode
            if c == ord('m') and not setup_lineal:
                setup_measure = not setup_measure
                usedoverlay = stream_update(setup_measure)
                continue

            #Lineal mode
            if c == ord('l') and not setup_measure and pixelper_unit != 0:
                setup_lineal = not setup_lineal
                usedoverlay = stream_update(False,setup_lineal)
                continue

            #Center Cursor
            if c == ord('c'):
                ui_cr_offset_x = 0
                ui_cr_offset_y = 0
                usedoverlay = stream_update()
                continue
         
            #Messure Movement slow
            if (c == curses.KEY_LEFT or c == curses.KEY_DOWN) and setup_measure:
                ui_ms_offset_x -= 1
                ui_ms_offset_y += 1
                usedoverlay = stream_update(True)
                continue
            if (c == curses.KEY_RIGHT or c == curses.KEY_UP) and setup_measure:
                ui_ms_offset_x += 1
                ui_ms_offset_y -= 1
                usedoverlay = stream_update(True)
                continue
            
            #Messure Movement fast
            if (c == 393 or c==336) and setup_measure:
                ui_ms_offset_x -= 50
                ui_ms_offset_y += 50
                usedoverlay = stream_update(True)
                continue
            if (c == 402 or c==337) and setup_measure:
                ui_ms_offset_x += 50
                ui_ms_offset_y -= 50
                usedoverlay = stream_update(True)
                continue

            #Lineal Movement slow
            if c == curses.KEY_LEFT and setup_lineal:
                ui_li_offset_x -= 1
                usedoverlay = stream_update(False,True)
                continue
            if c == curses.KEY_RIGHT and setup_lineal:
                ui_li_offset_x += 1
                usedoverlay = stream_update(False,True)
                continue
            if c == curses.KEY_UP and setup_lineal:
                ui_li_offset_y -= 1
                usedoverlay = stream_update(False,True)
                continue
            if c == curses.KEY_DOWN and setup_lineal:
                ui_li_offset_y += 1
                usedoverlay = stream_update(False,True)
                continue

            #Lineal Movement fast
            if c == 393 and setup_lineal:
                ui_li_offset_x -= 50
                usedoverlay = stream_update(False,True)
                continue
            if c == 402 and setup_lineal:
                ui_li_offset_x += 50
                usedoverlay = stream_update(False,True)
                continue
            if c == 337 and setup_lineal:
                ui_li_offset_y -= 50
                usedoverlay = stream_update(False,True)
                continue
            if c == 336 and setup_lineal:
                ui_li_offset_y += 50
                usedoverlay = stream_update(False,True)
                continue

            #Lineal Movement unit
            if c == 543 and setup_lineal:
                ui_li_offset_x -= pixelper_unit
                usedoverlay = stream_update(False,True)
                continue
            if c == 558 and setup_lineal:
                ui_li_offset_x += pixelper_unit
                usedoverlay = stream_update(False,True)
                continue
            if c == 564 and setup_lineal:
                ui_li_offset_y -= pixelper_unit
                usedoverlay = stream_update(False,True)
                continue
            if c == 523 and setup_lineal:
                ui_li_offset_y += pixelper_unit
                usedoverlay = stream_update(False,True)
                continue       
            
            #Cursor Movement slow
            if c == curses.KEY_LEFT:
                ui_cr_offset_x -= movement_incrementer(1,20,curses.KEY_LEFT)
                usedoverlay = stream_update()
                continue
            if c == curses.KEY_RIGHT:
                ui_cr_offset_x += movement_incrementer(1,20,curses.KEY_RIGHT)
                usedoverlay = stream_update()
                continue
            if c == curses.KEY_UP:
                ui_cr_offset_y -= movement_incrementer(1,20,curses.KEY_UP)
                usedoverlay = stream_update()
                continue
            if c == curses.KEY_DOWN:
                ui_cr_offset_y += movement_incrementer(1,20,curses.KEY_DOWN)
                usedoverlay = stream_update()
                continue

            #Cursor Movement fast
            if c == 393:
                ui_cr_offset_x -= 50
                usedoverlay = stream_update()
                continue
            if c == 402:
                ui_cr_offset_x += 50
                usedoverlay = stream_update()
                continue
            if c == 337:
                ui_cr_offset_y -= 50
                usedoverlay = stream_update()
                continue
            if c == 336:
                ui_cr_offset_y += 50
                usedoverlay = stream_update()
                continue

            #Cursor Movement unit
            if c == 543:
                ui_cr_offset_x -= pixelper_unit
                usedoverlay = stream_update()
                continue
            if c == 558:
                ui_cr_offset_x += pixelper_unit
                usedoverlay = stream_update()
                continue
            if c == 564:
                ui_cr_offset_y -= pixelper_unit
                usedoverlay = stream_update()
                continue
            if c == 523:
                ui_cr_offset_y += pixelper_unit
                usedoverlay = stream_update()
                continue

            #Cursor Offset
            if c == ord('+'):
                cr_o +=1
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue
            if c == ord('-') and cr_o > 0:
                cr_o -=1
                usedoverlay = stream_update(setup_measure,setup_lineal)
                continue

            #Overlay Alpha
            if c == ord(','):
                if overlay_alpha-10 > 0:
                    overlay_alpha-= 10
                    usedoverlay = stream_alphachange(usedoverlay,setup_measure,setup_lineal)
                elif overlay_alpha - 1 >= 0:
                    overlay_alpha-= 1
                    usedoverlay = stream_alphachange(usedoverlay,setup_measure,setup_lineal)
                continue

            if c == ord('.'):
                if overlay_alpha + 10 < 255:
                    overlay_alpha+= 10
                    usedoverlay = stream_alphachange(usedoverlay,setup_measure,setup_lineal)
                elif overlay_alpha + 1 <= 255:
                    overlay_alpha+= 1
                    usedoverlay = stream_alphachange(usedoverlay,setup_measure,setup_lineal)
                continue
            

except:
    e = sys.exc_info()[0]
    print("ERROR: " + str(e))
    curses.nocbreak(); stdscr.keypad(0); curses.echo()
    curses.endwin()
    camera.stop_preview()
    camera.close()
    sys.exit()


curses.nocbreak(); stdscr.keypad(0); curses.echo()
curses.endwin()
camera.stop_preview()
camera.close()
msg_positive("Raspberry Pi Camera Overlay erfolgreich beendet")
sys.exit()



