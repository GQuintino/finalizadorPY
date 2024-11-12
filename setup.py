from distutils.core import setup
import py2exe

setup(
    windows=[{"script": "updatepy.py"}],  # Nome do seu script principal
    options={
        "py2exe": {
            "includes": ["PyQt5.QtWidgets", "PyQt5.QtGui", "PyQt5.QtCore", "psycopg2"],
            "bundle_files": 1,  # Empacota tudo em um único executável
        }
    },
    zipfile=None,  # Evita a criação de um arquivo ZIP separado
)