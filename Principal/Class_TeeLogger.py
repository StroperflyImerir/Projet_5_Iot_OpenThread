import sys
import datetime

#==============================================================================================
# Class_TeeLogger.py
#==============================================================================================



class TeeLogger:
    
    @staticmethod
    def generate_log_filename(prefix="otns_log"):
        """Generate a log filename with current timestamp: prefix_YYYYMMDD_HHMMSS.txt"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.txt"
                                        
    def __init__(self, file_obj=None, filename=None):
        """
        Initialize TeeLogger with either an existing file object or a filename.
        If neither is provided, it creates a file with timestamp in the name.
        """
        if file_obj is not None:
            self.file_obj = file_obj
            self.filename = getattr(file_obj, 'name', 'unknown')
            self.should_close = False
        else:
            if filename is None:
                filename = self.generate_log_filename()
            self.filename = filename
            self.file_obj = open(filename, "w")
            self.should_close = True
        print(f"Logging to: {self.filename}")
                                        
    def write(self, data):
        # Si data est en bytes, le décoder en utf-8 (avec remplacement en cas d'erreur)
        if isinstance(data, bytes):
            data = data.decode("utf-8", errors="replace")
        sys.stdout.write(data)
        self.file_obj.write(data)
    
    def flush(self):
        sys.stdout.flush()
        self.file_obj.flush()
        
    def close(self):
        """Close the file if we opened it"""
        if self.should_close and self.file_obj is not None:
            self.file_obj.close()
            self.file_obj = None
            
    def __del__(self):
        """Ensure file is closed on garbage collection"""
        self.close()