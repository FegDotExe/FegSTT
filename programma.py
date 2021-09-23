import speech_recognition
import os
from json import load
from sys import exit as killini
from pydub import AudioSegment
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    program_path = os.path.dirname(sys.executable)+"/"
elif __file__:
    program_path = os.path.dirname(os.path.realpath(__file__)).replace("\\","/")+"/"

dir_path=str(Path(program_path).parent.absolute())+"/"

#Prep stuff
if not os.path.exists(program_path):
    os.makedirs(program_path)
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
if not os.path.exists(program_path+"temp_files/"):
    os.makedirs(program_path+"temp_files/")

recognitore=speech_recognition.Recognizer()


loop=True
while loop:
    nome_input=input("Inserisci il nome dell'audio (con estensione)\n>")
    if os.path.isfile(dir_path+nome_input):
        original_file=nome_input.split(".")
        loop=False
    else:
        print("\tSembra che questo file non esista nella stessa cartella del programma")

#Set ambient noise
ambient_noise=""
while ambient_noise not in ["y","n"]:
    ambient_noise=input("Utilizzare la riduzione del rumore per l'audio? (y=sì,n=no)\n>")
ambient_noise=True if ambient_noise=="y" else False

#Set ambient noise duration
if ambient_noise:
    loop=True
    while loop:
        ambient_noise_duration=input("Da 0 a 1, quanto dev'essere intensa la riduzione del rumore? (usare il punto per indicare la virgola)\n>")
        try:
            ambient_noise_duration=float(ambient_noise_duration)
            loop=False
        except:
            print("\tInserisci un numero valido")


nome_output=input("Inserisci il nome del file dove vuoi vengano salvati i testi (l'estensione verrà impostata automaticamnete come .txt)\n>")

different_format=False
print("──────\n┌Inizio dell'importazione del file audio")
if original_file[1]!="wav":
    print("│\t┌Inizio conversione a .wav per lettura corretta")
    wrong_audio=AudioSegment.from_file(dir_path+nome_input,format=original_file[1])
    wrong_audio.export(program_path+"temp_files/"+original_file[0]+".wav",format="wav")
    print("│\t└Fine conversione a .wav")
    file_audio = speech_recognition.AudioFile(program_path+"temp_files/"+original_file[0]+".wav")
    different_format=True
else:
    file_audio = speech_recognition.AudioFile(dir_path+nome_input)
print("└Fine dell'importazione del file audio")

with file_audio as source:
    print("┌Inizio dell'elaborazione del file audio")
    if ambient_noise:
        print("│\t┌Inizio riduzione del rumore")
        recognitore.adjust_for_ambient_noise(source,ambient_noise_duration)
        print("│\t└Fine riduzione del rumore")
    audio = recognitore.record(source)
    print("└Fine dell'elaborazione del file audio")
print("┌Inizio sintetizzazione del file audio")
try:
    testo=recognitore.recognize_google(audio,language="it-IT")
except:
    print("│\t┌Inizio riduzione del rumore a seguito di un errore di sintetizzazione")
    with file_audio as source:
        recognitore.adjust_for_ambient_noise(source)
        audio = recognitore.record(source)
        print("│\t│Secondo tentativo di sintetizzazione")
        testo=recognitore.recognize_google(audio,language="it-IT")
        print("│\t└Fine secondo tentativo di sintetizzazione")
print("└Fine sintetizzazione del file audio")

print("┌Inizio trascrizione del testo nel file %s.txt"%(nome_output))
output_file=open(dir_path+nome_output+".txt","w")
output_file.write(testo)
output_file.close()
if different_format:
    print("│\t┌Inizio rimozione file temporaneo")
    if os.path.exists(program_path+"temp_files/"+original_file[0]+".wav"):
        os.remove(program_path+"temp_files/"+original_file[0]+".wav")
    print("│\t└Fine rimozione file temporaneo")
input("└Fine trascrizione. Premere invio per uscire dal programma")
#recognitore.recognize_houndify(source)