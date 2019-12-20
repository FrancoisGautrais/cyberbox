
import pystache

def html_template(path, data):
    with open(path) as file:
        return pystache.render(file.read(), data)