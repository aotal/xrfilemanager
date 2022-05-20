import streamlit as st
import glob
import os
import struct
from shutil import copyfile

import numpy as np
import pandas as pd
import pydicom as dc
import re
from io import BytesIO

# Constantes y tolerancias

# Funciones


def NombreFichero(x): return os.path.splitext(
    x.replace(os.path.dirname(x) + "\\", ""))[0]


def Extension(x): return os.path.splitext(
    x.replace(os.path.dirname(x) + "\\", ""))[1]


def tipo(x): return 'AXIAL' if x == 0.0 else 'HELIX'

# Configuración


lista = {
    "siemens": {
        "Corte": "SliceLocation",
        "Espesor": "SliceThickness",
        "KVP": "KVP",
        "Corriente": "XRayTubeCurrent",
        "Tipo": "SpiralPitchFactor",
        "Exposicion": "Exposure",
        "Pixel": "PixelSpacing",
        "Kernel": "ImageType",
        "Protocolo": "BodyPartExamined",
    },
    "philips": {
        "Corte": "SliceLocation",
        "Espesor": "SliceThickness",
        "KVP": "KVP",
        "Corriente": "XRayTubeCurrent",
        "Tipo": "ScanOptions",
        "Exposicion": "Exposure",
        "Kernel": "ImageType",
        "Protocolo": "BodyPartExamined",
    },
}

# funciones

def CambioEnLoader(nombre, fichero):
    if 'context' in st.session_state:
        if nombre in st.session_state.context:
            if type(st.session_state[fichero]) is list:
                if (len(st.session_state[fichero]) == 0):
                    del st.session_state.context[nombre]
            else:
                del st.session_state.context[nombre]

def formatotput(X):
    if X.VR == "FD":
        # return struct.unpack("<d", X.value)[0]
        return X.value
    elif X.VR == "DS":
        try:
            if len(X.value) > 0:
                return X.value[0]
        except:
            return float(X.value)
    elif X.VR == "IS":
        return int(X.value)
    elif X.VR == "LO":
        return str(X.value)
    else:
        # return X.value.decode("ISO_IR 100")
        return X.value


def CleanFiles(route, lista):
    files = [
        X
        for X in glob.glob(route + "/**", recursive=True)
        if not os.path.isdir(X)
        and NombreFichero(X) != "thumbnail"
        and NombreFichero(X) != "Thumbs"
    ]
    for i, x in enumerate(files):
        dcm = dc.read_file(x)
        try:
            dcm.decompress()
            #ourPath=route + "/Img" + str(i) + "__Z="+str(dcm.SliceLocation)+"__Thk="+str(int(dcm.SliceThickness*10))+ "__tipo="+tipo(dcm.get_item(lista['siemens']['Tipo']))+".dcm"
            ourPath = route + "/Img" + str(i) + "__Z="+str(formatotput(dcm.get_item(lista['Corte'])))+"__Thk="+str(
                formatotput(dcm.get_item(lista['Espesor']))) + "__tipo="+tipo(formatotput(dcm.get_item(lista['Tipo'])))+".dcm"
            # print(ourPath)
            dc.write_file(ourPath, dcm)
            i = i + 1
        except:
            # print(dcm.Modality,x)
            ourPath = route+"/Img"+dcm.Modality+str(i)+".dcm"
            dc.write_file(ourPath, dcm)


def getTable(images, lista):
    output = []
    for X in images:
        img = dc.read_file(X)
        try:
            output.append(
                # [NombreFichero(X)]
                [X]
                + [formatotput(img[lista[X]]) for X in lista.keys()]
            )
        except:
            print("Valor no válido")

    return pd.DataFrame(output, columns=["Nombre"] + list(lista.keys())).astype(
        {
            "Corte": float,
            "Espesor": float,
            "KVP": float,
            "Corriente": float,
            "Tipo": float,
            "Exposicion": str,
            "Pixel": float,
            "Kernel": str,
            "Protocolo": str
        }
    )



st.title('File Manager')


# Espesor de corte

st.markdown(
    '## Prueba de descompresión de ficheros')

input_file1_raw = st.file_uploader(
    "", None, True, key='input_file1_raw', help="Prueba de descompresión")
#TC007_table_axial = np.zeros((1, 3))

if input_file1_raw is not None:
    files1 = [dc.read_file(x) for x in input_file1_raw]
if len(files1) > 0:
   #files1[0].decompress()
   st.write(files1[0].SliceThickness)
   out = BytesIO()
   a=files1[0].decompress()
   files1[0].save_as(out)
   st.download_button('Download dcm', a, file_name='aa.dcm')