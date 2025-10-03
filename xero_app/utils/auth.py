import base64

def basic_auth_header(client_id, client_secret):
    b = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(b).decode("utf-8")
