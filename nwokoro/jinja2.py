from jinja2 import Environment as Jinja2Environment
from jinja2 import FileSystemLoader, select_autoescape
import os
from django.urls import reverse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def Environment(**options):
    app_template_dirs = [
        os.path.join(BASE_DIR, app_path, 'templates') 
        for app_path in os.listdir(BASE_DIR) 
        if os.path.isdir(os.path.join(BASE_DIR, app_path))
    ]
    env = Jinja2Environment(
        loader=FileSystemLoader(app_template_dirs),
        autoescape=select_autoescape(['html', 'xml']),
        **options
    )
    # Add the 'url' function
    env.globals.update({
        'url': reverse,
    })
    
    return env

