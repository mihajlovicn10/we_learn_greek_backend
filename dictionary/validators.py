import re 
from django.core.exceptions import ValidationError 

def validate_greek(value): 
    
    regex = r'^(ο|η|το)? ?[Α-Ωα-ωίϊΐόάέύϋΰήώΆΈΉΊΪΊΌΎΫΏ]+$'
    
    if not re.fullmatch(regex, value): 
        raise ValidationError("The Greek word must contain only Greek alphabet characters.")
    