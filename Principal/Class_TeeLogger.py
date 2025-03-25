
import sys


#==============================================================================================
# Class_TeeLogger.py
#==============================================================================================



class TeeLogger:
                                        
    def __init__(self, file_obj):
        self.file_obj = file_obj
                                        # write() est une méthode qui écrit une chaîne de caractères
    def write(self, data):
        # Si data est en bytes, le décoder en utf-8 (avec remplacement en cas d'erreur)
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        sys.stdout.write(data)
        self.file_obj.write(data)
    
                                       # flush() est une méthode qui vide le tampon de sortie
    def flush(self):
        sys.stdout.flush()
        self.file_obj.flush()