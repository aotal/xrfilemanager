import streamlit as st
import glob
import os
import struct
from shutil import copyfile
#import gdcm

import numpy as np
import pandas as pd
import pydicom as dc
import re
from io import BytesIO
import json
from st_aggrid import AgGrid
from st_aggrid import GridUpdateMode, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

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

@st.cache(suppress_st_warning=True)
def selectwidget(X, table, lista):
    if lista[X]['type'] == 'U':
        out = st.selectbox(X, pd.unique(table[X]))
    elif lista[X]['type'] == 'D':
        out = st.slider(X, float(table[X].min()), float(
            table[X].max()), (float(table[X].min()), float(table[X].max())))
    return out


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
    for img in images:
        try:
            output.append(
                # [NombreFichero(X)]
                [formatotput(img[lista[X]['value']]) for X in lista.keys()]
            )
        except:
            print("Valor no válido")
    print({x:lista[x]['format'] for x in lista.keys()})
    return pd.DataFrame(output, columns=list(lista.keys())).astype({x:lista[x]['format'] for x in lista.keys()})


def FillArray(X):
    files1 = []
    for x in X:
        try:
            s = dc.read_file(x)
            s.decompress()
            files1.append(s)
        except:
            pass
    return files1


st.title('File Manager')

# Barra lateral
st.sidebar.header('Configuración de los filtros')
json_fields_dcm = st.sidebar.file_uploader("JSON de configuración", [
                                           'json'], False, key='json_fields_dcm', help='Fichero json donde se especifican los campos dicom que interesan para filtrar')
if json_fields_dcm is not None:
    with open(json_fields_dcm.name) as fp:
        data_table = json.load(fp)

# Espesor de corte

st.markdown(
    '## Prueba de descompresión de ficheros')

input_file1_raw = st.file_uploader(
    "", None, True, key='input_file1_raw', help="Prueba de descompresión")
#TC007_table_axial = np.zeros((1, 3))

if input_file1_raw is not None:
    files1 = FillArray(input_file1_raw)
    #files1 = [dc.read_file(x) for x in input_file1_raw]
if len(files1) > 0 and json_fields_dcm is not None:

    TableMaster = getTable(files1, data_table)

    gb = GridOptionsBuilder.from_dataframe(TableMaster)
    # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
    gb.configure_default_column(enablePivot=True, enableValue=True, enableRowGroup=True)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar()  # side_bar is clearly a typo :) should by sidebar
    gridOptions = gb.build()


    response = AgGrid(
    TableMaster,
    gridOptions=gridOptions,
    enable_enterprise_modules=True,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    fit_columns_on_grid_load=False,)

    df = pd.DataFrame(response["selected_rows"])
    st.dataframe(df)
   #out = BytesIO()
   # files1[0].save_as(out)
   #st.download_button('Download dcm',out, file_name='aa.dcm')
    # st.dataframe(TableMaster)
    #widgets=[]
    #for x in data_table.keys():
    #    widgets.append(selectwidget(x, TableMaster, data_table))
    #a = selectwidget('Corte', TableMaster, data_table)
    #espesor=st.selectbox("Elegir espesor",pd.unique(TableMaster['Espesor']))
