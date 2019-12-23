import pystache

def html_template(path, data):
    with open(path) as file:
        return pystache.render(file.read(), data)

def html_template_string(source, data):
    return pystache.render(source, data)