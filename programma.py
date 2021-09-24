import speech_recognition
import os
from json import load, dumps, dump
from sys import exit as killini
from pydub import AudioSegment 
from pydub.silence import split_on_silence
import sys
from pathlib import Path
from time import sleep
from traceback import format_exc

if getattr(sys, 'frozen', False):
    program_path = os.path.dirname(sys.executable)+"/"
elif __file__:
    program_path = os.path.dirname(os.path.realpath(__file__)).replace("\\","/")+"/"

def jread(relative_path):
    with open(program_path+relative_path,encoding="utf-8") as fail:
        data=load(fail)
    return data
def jwrite(relative_path,data):
    with open(program_path+relative_path,"w") as fail:
        fail.write(dumps(data,indent=4))
        fail.close()
settings_dict=jread("settings.json")

dir_path=str(Path(program_path).parent.absolute())+"/"

#Prep stuff
if not os.path.exists(program_path):
    os.makedirs(program_path)
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
if not os.path.exists(program_path+"temp_files/"):
    os.makedirs(program_path+"temp_files/")

for f in os.listdir(program_path+"temp_files/"):
    if os.path.exists(program_path+"temp_files/"+f):
        os.remove(program_path+"temp_files/"+f)

recognitore=speech_recognition.Recognizer()

loop=True
while loop:
    nome_input=input("Inserisci il nome dell'audio (con estensione) oppure premi invio per modificare le impostazioni\n>")
    if os.path.isfile(dir_path+nome_input):
        original_file=nome_input.split(".")
        loop=False
    elif nome_input=="":
        modify_target=""
        while modify_target not in ["0","1","2"]:
            modify_target=input("Digita il numero corrispondente alla proprietà che desideri modificare\n0=Durata minima del silenzio perché il file audio venga diviso\n1=Intensità del silenzio in dBFS\n2=Stringa posta al termine di un segmento\n>")
        if modify_target=="0":
            loopi=True
            print("I file audio lunghi vengono divisi in sezioni in modo da essere più facili da processare.\nIl valore che si sta modificando equivale a quanti millisecondi deve durare un momento di silenzio perché il programma usi la pausa come divisione.\nIl valore consigliato è di 500; Il valore attuale è di %i.\nDigitare il valore oppure premere invio per mantenere il valore attuale"%(settings_dict["Split silence"]))
            while loopi:
                silence_amount=input(">")
                if silence_amount!="":
                    try:
                        silence_amount=int(silence_amount)
                        settings_dict["Split silence"]=silence_amount
                        jwrite("settings.json",settings_dict)
                        loopi=False
                    except:
                        pass
                else:
                    loopi=False
        elif modify_target=="1":
            loopi=True
            print("I file audio lunghi vengono divisi in sezioni in modo da essere più facili da processare.\nIl valore che si sta modificando equivale al livello di volume in dBFS che viene considerato silenzio.\nIl valore consigliato è di -36; Il valore attuale è di %i.\nDigitare il valore oppure premere invio per mantenere il valore attuale"%(settings_dict["Split audio"]))
            while loopi:
                this_input=input(">")
                if this_input!="":
                    try:
                        this_input=int(this_input)
                        settings_dict["Split audio"]=this_input
                        jwrite("settings.json",settings_dict)
                        loopi=False
                    except:
                        pass
                else:
                    loopi=False
        elif modify_target=="2":
            loopi=True
            print("I file audio lunghi vengono divisi in sezioni in modo da essere più facili da processare.\nIl valore che si sta modificando equivale a ciò che viene scritto nel testo al termine di un segmento.\nVa tenuto presente che \\n significa 'a capo'.\nIl valore consigliato è \\n; Il valore attuale è %s.\nDigitare il valore oppure premere invio per mantenere il valore attuale"%(settings_dict["Section end"].replace("\n","\\n")))
            while loopi:
                this_input=input(">")
                if this_input!="":
                    try:
                        settings_dict["Section end"]=this_input.replace("\\n","\n")
                        jwrite("settings.json",settings_dict)
                        loopi=False
                    except:
                        pass
                else:
                    loopi=False
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

print("──────\n┌Inizio dell'importazione del file audio")
file_audio=AudioSegment.from_file(dir_path+nome_input,format=original_file[1])
print("└Fine dell'importazione del file audio")

print("┌Inizio divisione del file audio a silenzi con parametri di %i per durata e %i per intensità (ci vuole sempre un bel po')"%(settings_dict["Split silence"],settings_dict["Split audio"]))
chunks_of_audio=split_on_silence(file_audio,min_silence_len=settings_dict["Split silence"],silence_thresh=settings_dict["Split audio"])
print("└Fine divisione del file audio (%i segmenti ottenuti)"%(len(chunks_of_audio)))
output_file=open(dir_path+nome_output+".txt","w+")
i=0
failed=0
print("┌Inizio elaborazione dei segmenti")
for audio_chunk in chunks_of_audio:
    print("│\t┌Inizio elaborazione del segmento %i/%i-%i"%(i+1,len(chunks_of_audio),int((100*(i+1))/len(chunks_of_audio)))+"%")

    audio_chunk=AudioSegment.silent(duration=500)+audio_chunk+AudioSegment.silent(duration=500)
    audio_chunk.export(program_path+"temp_files/chunk%i.wav"%(i),format="wav")

    with speech_recognition.AudioFile(program_path+"temp_files/chunk%i.wav"%(i)) as source:
        if ambient_noise:
            recognitore.adjust_for_ambient_noise(source,ambient_noise_duration)

        audio_ascoltato=recognitore.record(source)
        retry=True
        ii=0
        print("│\t│\t┌Inizio trascrizione audio")
        while retry and ii<5:
            try:
                testo=recognitore.recognize_google(audio_ascoltato,language="it-IT")
                retry=False
                output_file.write(testo+settings_dict["Section end"])
            except speech_recognition.UnknownValueError:
                print("│\t│\t┆Testo non riconosciuto")
                retry=False
            except Exception as e:
                if ii<4:
                    print("│\t│\t├Errore di connessione. Si ripeterà il tentativo tra 5 secondi.")
                    sleep(5)
                ii+=1
                if ii==5:
                    if not os.path.exists(dir_path+"failed_files/"):
                        os.makedirs(dir_path+"failed_files/")
                    print("│\t│\t├Esportazione del file audio tra i file non trascritti.")
                    audio_chunk.export(dir_path+"failed_files/%s.%s-chunk-%i.wav"%(original_file[0],original_file[1],i+1),format="wav")
                    output_file.write("[TRASCRIZIONE FALLITA PER AUDIO %s.%s-chunk-%i.wav]"%(original_file[0],original_file[1],i+1)+settings_dict["Section end"])
                    failed+=1
        print("│\t│\t└Fine trascrizione audio")
        try:
            os.remove(program_path+"temp_files/chunk%i.wav"%(i))
        except:
            pass
    print("│\t└Fine elaborazione del segmento")
    i+=1
input("└Fine elaborazione dei segmenti. Il risultato è stato salvato in %s.txt\nA causa di problemi di connessione o di file troppo estesi, non è stato possibile trascrivere %i file.\nSi possono ascoltare i file non trascritti nella cartella failed_files\nPremere invio per chiudere il programma"%(nome_output,failed))