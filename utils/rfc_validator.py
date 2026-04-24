import re
import datetime
from dateutil.parser import parse


class RFCError(Exception):
    """Exception raised for custom error in the application."""
    pass

class InvalidDateError(RFCError):
    def __init__(self,date, message = "Invalid date format yymmdd expected"):
        super().__init__(f"{message} , {date} obtained")

class InvalidInitialsError(RFCError):
    def __init__(self,tipo, message = "Invalid initials obtained"):
        initials  = ("XXX","XXXX")[tipo == "fisica"]
        super().__init__(f"{message} , {initials} expected")

class InvalidTipo(RFCError):
    def __init__(self,tipo, message = "Invalid tipo obtained"):
        super().__init__(f"{message} , 'fisica'/'moral' expected, {tipo} obtained")

class InvalidLen(RFCError):
    def __init__(self, message = "Invalid rfc lenght"):
        super().__init__(f"{message}")
        
class InvalidFormat(RFCError):
    def __init__(self,rfc, message = "Invalid RFC format obtained , expected: ^([A-ZÑ&]{3,4})(\d{6})([A-Z0-9]{3})$"):
        super().__init__(f"{message}, {rfc} obtained")
    
    
def validar_rfc(rfc,tipo):

    if(rfc == None):
        raise InvalidLen
    
    if(tipo == "fisica"):

        if(len(rfc) != 13):
            raise InvalidLen
        
        rfc = rfc.upper().strip()
        
        pattern = r"^([A-ZÑ&]{3,4})(\d{6})([A-Z0-9]{3})$"

        if (re.fullmatch(pattern,rfc) == None):
            raise InvalidFormat(rfc)
        
        date = rfc[4:10]
        year = date[:2]
        year = int(year)
        

        if( 30 >= year >= 0):
            year = 2000 + year
        else:
            year = 1900 + year

        date =  str(year) + date[2:]

        try:
            parse(date)

        except:
            raise InvalidDateError(date)

        return True

    if(tipo == "moral"):
        pass
    
    else:
        raise InvalidTipo(tipo)
