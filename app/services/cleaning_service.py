import re

def clean(text:str)->str:
    if not isinstance(text, str):
        raise TypeError("Expected text to be a string.")

    text = _normalize_line_endings(text)
    text = _remove_trailing_whitespace(text)
    text = _collapse_multiple_spaces(text)
    text = _collapse_blank_lines(text)
    text = _trim_document(text)

    return text

def _normalize_line_endings(text:str)->str:
    #Converts line endings to unix format
    #Windows and old mac line style to Unix line style
    
    return text.replace("\r\n","\n").replace("\r","\n")

def _remove_trailing_whitespace(text:str)->str:
    #Removes unnecessary spaces btw lines
    return "\n".join( 
        line.rstrip() #RIGHT STRIP:removes useless on the right side of line
        for line in text.split("\n") #splits into diff line when \n found
    )

def _collapse_multiple_spaces(text:str)->str:
    #Multiple spaces to a single spaces

    return re.sub(r"[\t]+", " ",text) #re.sub = Find nd Replace

def _collapse_blank_lines(text:str)->str:
    #Multiple blank lines to single blank line

    return re.sub(r"\n{3,}","\n\n",text)

def _trim_document(text:str)->str:
    #Removes extra spaces from start and end of a text

    return text.strip()