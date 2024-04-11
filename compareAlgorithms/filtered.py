from filters import *

def get_filtered(issue):
    title = issue['title'] if issue['title'] != None else ''
    body = issue['body'] if issue['body'] != None else ''

    title = toLowercase(title)
    title = filterLinks(title)
    title = filterDigits(title)
    title = filterStopWords(title)
    
    body = toLowercase(body)
    body = filterLinks(body)
    body = filterDigits(body)
    body = filterStopWords(body)
    
    title_body = f"{title} {body}"
        
    return title_body