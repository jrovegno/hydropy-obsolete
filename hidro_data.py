#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       hidro_data.py
#       
#       Copyright 2010 Javier Rovegno Campos <javier.rovegno@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
"""Librería python para hidrología computacional.
   @author: Javier Rovegno
   @contact: javier.rovegno@gmail.com
   @version: 0.1
   @license: GNU General Public License
   
   Website: U{http://code.google.com/p/hydropy/}
"""

import datetime
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import warnings  # DeprecationWarning: scipy.stats.mean
warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    import xlrd
except ImportError:
    warnings.warn("from_xls no funciona sin instalar python-xlrd",RuntimeWarning)
try:
    import xlwt
except ImportError:
    warnings.warn("to_xls no funciona sin instalar python-xlwt",RuntimeWarning)

def from_xls(archivo,nsheet=0):
    """
    Genera una matriz de datos a partir de un archivo excel.
    @param archivo: Datos mensuales o anuales.
    @type archivo: excel file
    @param nsheet: Indice de la hoja del archivo excel
    @type nsheet: int
    @return: Matriz de datos mensuales A o anuales B
    
        Descripcción de matriz de datos::
            A[0] lista de años con datos
            A[0][0] 1er año con datos
            A[1] submatriz de datos por año
            A[1][0] lista con datos mensuales 1er año
            A[1][0][0] dato 1er año 1er mes
            A[2] lista de etiqueta datos
            A[2][1] etiqueta 1er dato
            
            B[0] lista de años con datos
            B[0][0] 1er año con datos
            B[1] lista de datos por año
            B[1][0] dato 1er año
            B[2] lista de etiqueta datos
            B[2][1] etiqueta 1er dato
    @rtype: Matriz de datos
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls') # Lee sheet 0 (mensual)
    >>> a[0]
    [1950.0, 1951.0, 1952.0]
    >>> b = from_xls('data_test.xls',1) # Lee sheet anual
    >>> b[1][0]
    [1.1000000000000001]
    >>> from_xls('data_test.xls',-1) # Lee sheet fuera de rango
    Traceback (most recent call last):
    ...
    ValueError: nsheet fuera de rango
    >>> from_xls('data_test.xls','hola') # Indice sheet str
    Traceback (most recent call last):
    ...
    ValueError: nsheet debe ser un entero
    """
    if type(nsheet) != int:
        raise ValueError, "nsheet debe ser un entero"
    book = xlrd.open_workbook(archivo)
    if range(book.nsheets).count(nsheet) == 0:
        raise ValueError, "nsheet fuera de rango"
    sheet = book.sheet_by_index(nsheet) # Abre de acuerdo indice Hoja
    yrs_data = sheet.col_values(0,1) # Elimina 1era fila etiqueta
    label_data = sheet.row_values(0) # fila etiquetas
    valores = []
    for rx in xrange(1,sheet.nrows): # Eliminar 1era fila etiqueta
        valores.append(sheet.row_values(rx,1,sheet.ncols)) # Elimina
    return yrs_data,valores,label_data                    # col años

# Guarda la matriz de datos en un archivo excel
def to_xls(data,file_name='file01.xls',sheet_name='Hoja0'):
    """
    Escribe el contenido de una matriz de datos en
    un archivo de planilla de cálculo
    @param data: Matriz de datos
    @return: Archivo de planilla de cálculo xls
    @rtype: excel file
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls',0)
    >>> to_xls(a,'data_test_copy.xls')
    >>> b = from_xls('data_test_copy.xls')
    >>> a == b
    True
    """
    wb = xlwt.Workbook()
    ws = wb.add_sheet(sheet_name)
    # Caso rd_data_col
    if type(data[1][0]) != list and len(data[0]) == len(data[2]):
        for rx in xrange(len(data[0])):
            ws.write(rx+1, 0, data[0][rx])
            ws.write(rx+1, 1, data[1][rx])
            ws.write(rx+1, 2, data[2][rx])
    # TODO Caso rd_col
    # Caso datos anuales
    elif type(data[1][0]) != list:
        # Escribir label
        for cx in xrange(len(data[2])):
            ws.write(0, cx, data[2][cx])
        # Escribir yr,datos
        for rx in xrange(len(data[0])):
            ws.write(rx+1, 0, data[0][rx])
            ws.write(rx+1, 1, data[1][rx])
    # Caso datos mensuales
    else:
        # Escribir label
        for cx in xrange(len(data[2])):
            ws.write(0, cx, data[2][cx])
        # Escribir yr
        for rx in xrange(len(data[0])):
            ws.write(rx+1, 0, data[0][rx])
        # Escribir datos
        for rx in xrange(len(data[1])):
            for cx in xrange(len(data[1][rx])):
                ws.write(rx+1, cx+1, data[1][rx][cx])
    wb.save(file_name)


# Transforma la matriz de datos en un vector de datos
# TODO refactorizar
def rd_data_col(data,cx=None,lost_OK=False):
    """ Genera una matriz con datos de la columna cx
    Si no se especifica cx genera una matriz con todos los datos
    en una sola columna.
    Los años y etiquetas concuerdan con los del dato de la columna cx.
    @param data: Matriz de datos
    @param cx: Indice de la columna a leer
        Si cx=None extra todas las columnas 
    @type cx: int
    @return: Matriz de datos con la columna especificada
    @rtype: Matriz de datos
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls') # Lee sheet 0 (mensual)
    >>> [a[1][0][11],a[1][1][11],a[1][2][11]]
    [12.1, 13.1, '']
    >>> rd_data_col(a,11)[1] # Datos Diciembre
    [12.1, 13.1]
    >>> rd_data_col(a,11,lost_OK=True)[1] # Datos Diciembre
    [12.1, 13.1, '']
    >>> rd_data_col(a,0)[1] # Datos enero
    [1.1000000000000001, 2.1000000000000001, 3.1000000000000001]
    >>> rd_data_col(a,0)[2]
    [u'YEAR', u'JAN']
    >>> rd_data_col(a,0)[3]
    [u'JAN', u'JAN', u'JAN']
    >>> rd_data_col(a,0)[0]
    [1950.0, 1951.0, 1952.0]
    """
    valores = []
    yrs_data = []
    label_data_in = data[2][1:] # Elimina etiqueta u'Year'
    label_data = [data[2][0]] # Agrega etiqueta u'Year'
    label_data_c = []
    # Caso extrae todos los datos a una columna
    if cx == None:
        for rx in xrange(len(data[1])):
            # Caso matriz de datos con solo 1 columna
            if type(data[1][0]) != list:
                # No agrega fila con datos faltantes
                if data[0][rx] != '':
                    valores.append(data[1][rx])
                    yrs_data.append(data[0][rx])
                    label_data_c.append(label_data_in[0])
                # Agrega fila con datos faltantes sólo si se solicita explicitamente
                elif lost_OK:
                    valores.append(data[1][rx])
                    yrs_data.append(data[0][rx])
                    label_data_c.append(label_data_in[0])
                # Añade etiqueta de la columna
                if rx == 0:
                    label_data.append(label_data_in[0])
            # Caso matriz de datos todas las columnas
            else:
                for cx in xrange(len(data[1][0])):
                    # No agrega datos faltantes
                    if data[1][rx][cx] != '':
                        valores.append(data[1][rx][cx])
                        yrs_data.append(data[0][rx])
                        label_data_c.append(label_data_in[cx])
                    # Agrega datos faltantes sólo si se solicita explicitamente
                    elif lost_OK:
                        valores.append(data[1][rx][cx])
                        yrs_data.append(data[0][rx])
                        label_data_c.append(label_data_in[cx])
                    # Añade etiqueta de la columna
                    if rx == 0:
                        label_data.append(label_data_in[cx])
    # Caso cx no es un entero
    elif type(cx) != int:
        raise ValueError, "cx no válido"
    # Caso matriz de datos con solo 1 columna
    elif cx == 0 and type(data[1][0]) != list:
        for rx in xrange(len(data[1])):
            if data[0][rx] != '':
                valores.append(data[1][rx])
                yrs_data.append(data[0][rx])
                label_data_c.append(label_data_in[0])
            # Agrega fila con datos faltantes sólo si se solicita explicitamente
            elif lost_OK:
                valores.append(data[1][rx])
                yrs_data.append(data[0][rx])
                label_data_c.append(label_data_in[0])
            # Añade etiqueta de la columna
            if rx == 0:
                label_data.append(label_data_in[0])
    # Caso extrae los datos la columna cx
    elif 0 <= cx < len(data[1][0]):
        for rx in xrange(len(data[1])):
            # No agrega datos faltantes
            if data[1][rx][cx] != '':
                valores.append(data[1][rx][cx])
                yrs_data.append(data[0][rx])
                label_data_c.append(label_data_in[cx])
            # Agrega datos faltantes sólo si se solicita explicitamente
            elif lost_OK:
                valores.append(data[1][rx][cx])
                yrs_data.append(data[0][rx])
                label_data_c.append(label_data_in[cx])
            if rx == 0:
                label_data.append(label_data_in[cx])
    else:
        raise ValueError, "cx fuera de rango"
    return yrs_data,valores,label_data,label_data_c

# Transforma la matriz de datos en un vector de datos
def rd_col(data,cx=None):
    """ Genera una matriz con datos de la columna cx
    Si no se especifica cx genera una matriz con todos los datos
    en una sola columna
    @param data: Matriz de datos
    @param cx: Indice de la columna a leer
        Si cx=None extra todas las columnas 
    @return: Matriz de datos con la columna especificada
    @rtype: Matriz de datos
    @note: Obsoleto preferir rd_data_col
    """
    valores = []
    yrs_data = []
    label_data_in = data[2][1:] # Elimina etiqueta u'Year'
    label_data = []
    if cx == None:
        for rx in xrange(len(data[1])):
            for cx in xrange(len(data[1][0])):
                valores.append(data[1][rx][cx])
                yrs_data.append(data[0][rx])
                label_data.append(label_data_in[cx])
        return (yrs_data, 
                valores, 
                [u'Year',[u'Value',u'Month']], 
                label_data)
    elif type(cx) != int:
        raise ValueError, "cx no válido"
    elif 0 <= cx < len(data[1][0]):
        label_data.append(data[2][0])
        label_data.append(label_data_in[cx])
        for rx in xrange(len(data[1])):
             valores.append(data[1][rx][cx])
             yrs_data.append(data[0][rx])
        return yrs_data,valores,label_data
    else:
        raise ValueError, "cx fuera de rango"
        

# Transforma matriz de datos de año calendario a hidrológico
def hidro_yr(data,estiaje=4):
    """
    Transforma matriz de datos mensuales
    desde Año calendario a Año hidrológico
    @param data: Matriz de datos
    @param estiaje: Mes más seco del año a partir de los datos históricos
    @type estiaje: entero entre (1 ... 12) Enero a Diciembre
    @return: Matriz de datos transformados a año hidrológico
    @rtype: Matriz de datos
    """
    iestiaje = estiaje - 1
    valores = []
    yrs_data = []
    # Rellena label
    label_data = [data[2][0]]   # Etiqueta de Yr
    for cx in xrange(iestiaje+1,len(data[2])):
        label_data.append(data[2][cx])
    for cx in xrange(1,iestiaje+1):
        label_data.append(data[2][cx])
    # Rellena valores y años
    for rx in xrange(len(data[1])-1):       # Ultimo año se omite
        valores_yr = data[1][rx][iestiaje:]  # A partir del estiaje
        yrs_data.append(data[0][rx])        # Año inicio estiaje
        for cx in xrange(iestiaje):
            valores_yr.append(data[1][rx+1][cx])    # Hasta estiaje
        valores.append(valores_yr)                  # prox año
    return yrs_data,valores,label_data

# Crea un vector de datos con volúmen anual
def vol_yr(data,years=None):
    """ Crea un vector de datos con volumen anual
    @param data: Matriz de datos
    @type data: Datos de caudales mensuales
    @return: Datos de volúmenes anuales
    @rtype: Matriz de datos
    """
    valores = []
    yrs_data = []
    seg_day = 60 * 60 * 24.0
    MM = 1.0e6
    label_data = [data[2][0], u'Vol[MMm3]']
    meses = {u'JAN':1, u'FEB':2, u'MAR':3, u'APR':4,
             u'MAY':5, u'JUN':6, u'JUL':7, u'AUG':8, 
             u'SEP':9, u'OCT':10, u'NOV':11, u'DEC':12}
    if years == None:
        years = data[0]
    if type(years) != list: # Caso arg es un sólo año
        years = [years]
    for year in years:            
        rx = data[0].index(year)
        if data[1][rx].count('') == 0:
            year = data[0][rx]
            yrs_data.append(year)
            sum = 0.0
            for cx in range(len(data[1][rx])):
                mes = meses[data[2][cx+1]]      # data[2][0] = u'YEAR'
                first_day = datetime.date(year, mes, 1)
                if mes == 12:
                    year += 1
                    last_day = datetime.date(year, 1, 1)
                else:
                    last_day = datetime.date(year, mes+1, 1)
                delta_day = last_day - first_day
                sum = sum + data[1][rx][cx] * delta_day.days * seg_day                    
            valores.append(sum / MM)
    return yrs_data,valores,label_data
    
    
# Extrae los datos de un año específico
def yr(data,year,fill=None):
    """
    Extrae los datos de un año especificado
    @param data: Matriz de datos mensuales
    @type data: Matriz de datos
    @param year: Año especificado
    @type year: int
    @return: Datos mensuales del año especificado
    @rtype: list
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls', 2) # Lee sheet lost
    >>> yr(a, 1950)
    ['', 2.1000000000000001, 3.1000000000000001, 4.0999999999999996, 5.0999999999999996, 6.0999999999999996, 7.0999999999999996, 8.0999999999999996, '', 10.1, 11.1, 12.1]
    >>> yr(a, 1950,-9999)
    [-9999, 2.1000000000000001, 3.1000000000000001, 4.0999999999999996, 5.0999999999999996, 6.0999999999999996, 7.0999999999999996, 8.0999999999999996, -9999, 10.1, 11.1, 12.1]
    """
    iyear = data[0].index(year)
    if data[1][iyear].count('') == 0:
        return data[1][iyear]
    else:
        aux = []
        for cx in range(len(data[1][iyear])):
            if data[1][iyear][cx] == '' and fill != None:
                aux.append(fill)   # Si no hay dato pone fill
            else:
                aux.append(data[1][iyear][cx])
        return aux
    

# Calcula el max, media y min de una matriz de datos
def stad(data,cx=None):
    """  Calcula el max, media y min de una matriz de datos
    @param data: Matriz de datos
    @param cx: Indice de la columna
    @return: (max, media, min)
    @rtype: tuple
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls') # Lee sheet 0 (mensual)
    >>> stad(a)
    (13.1, 6.7666666666666639, 1.1000000000000001)
    """
    data_c = rd_data_col(data,cx)[1]    # Utiliza la Fn rd_data_col
    aux = np.asarray(data_c, dtype='float64')
    return aux.max(),aux.mean(),aux.min()
        
def quartil(data,cx=None):
    """  De una matriz de datos return (1er_quartil, 4to_quartil)
    @param data: Matriz de datos
    @param cx: Indice de la columna
    @return: (1er_quartil, 4to_quartil)
    @rtype: tuple
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls',0) # Lee sheet 0 (mensual)
    >>> a = concurrent(a,a) # Extrae años completos
    >>> vol_a = vol_yr(a) # Calcula el volumen anual
    >>> quartil(vol_a)
    (216.8424, 232.61040000000003)
    """
    data_c = rd_data_col(data,cx)[1]    # Utiliza la Fn rd_data_col    
    # Agrega primer cuartil
    quartil_1 = stats.scoreatpercentile(data_c,25)
    # Agrega cuarto cuartil
    quartil_4 = stats.scoreatpercentile(data_c,75)
    # quartil_1 retorna array([ valor])
    return quartil_1, quartil_4
        
    
# Clasifica por tipo de año (seco, normal, húmedo)
def yrs_type(data_vol,vol_hi=None,vol_low=None, is_data=False):
    """ Retorna matriz de listas con Años secos, Años normales, Años húmedos
    @param data_vol: Matriz de datos
    @type data_vol: Volúmenes anuales
    @param vol_hi: Volumen mínimo anual de un año húmedo
    @param vol_low: Volumen máximo anual de un año seco
    @param is_data: Si es True el parámetro data_vol es un matriz de datos
        con caudales mensuales
    @return: [Años secos, Años normales, Años húmedos]
    @rtype: list
    """
    dry_yrs = []
    normal_yrs = []
    wet_yrs = []
    if is_data:
        data_vol = vol_yr(data_vol) # Fn vol_yr
    if vol_hi == None and vol_low == None:
        vol_low , vol_hi = quartil(data_vol)   # Utiliza Fn quartil
        
    for rx in xrange(len(data_vol[0])):
        if data_vol[1][rx] <= vol_low:
            dry_yrs.append(data_vol[0][rx])
        elif data_vol[1][rx] < vol_hi:
            normal_yrs.append(data_vol[0][rx])
        else:
            wet_yrs.append(data_vol[0][rx])
    return dry_yrs,normal_yrs,wet_yrs

# Datos faltantes objeto data
def index_lost(data,yrx=True,hidecx=False):
    """  Entrega índices de datos faltantes
    @param data: Matriz de datos
    @param yrx: Si es True entrega el índice de la fila, 
        si es False entrega el año del dato faltante
    @param hidecx: Si es True agrega el índice de la columna
    @return: Lista de índices
    @rtype: list
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls', 2) # Lee sheet lost
    >>> index_lost(a)
    [[1950.0, 0], [1950.0, 8], [1951.0, 7], [1952.0, 11]]
    >>> index_lost(a, hidecx=True) # Lo mismo yr_index_lost
    [1950.0, 1951.0, 1952.0]
    >>> index_lost(a,yrx=False, hidecx=True) # Indice años faltantes
    [0, 0, 1, 2]
    >>> b = from_xls('data_test.xls', 1) # Lee sheet anual
    >>> index_lost(b, hidecx=True)
    [1952.0]
    >>> c = from_xls('data_test.xls', 0) # Lee sheet mensual    
    >>> index_lost(c, yrx=False, hidecx=False)
    [[2, 3], [2, 4], [2, 5], [2, 6], [2, 7], [2, 8], [2, 9], [2, 10], [2, 11]]
    """
    valores = []    
    for rx in range(len(data[1])):
        for cx in range(len(data[1][rx])):
            if data[1][rx][cx] == '':
                if yrx and hidecx == False:
                    valores.append([data[0][rx],cx])
                elif yrx and hidecx:
                    valores.append(data[0][rx])
                    break ## No busca más dentro del año
                elif yrx == False and hidecx == False:
                    valores.append([rx,cx])                    
                elif yrx == False and hidecx:
                    valores.append(rx)
    return valores

# Datos concurrentes
def concurrent(data1,data2=None):
    """ Compara años completos recurrentes de 2 matrices de datos
    @param data1: Matriz de datos
    @param data2: Matriz de datos
    @return: Matriz de datos de data1 recurrentes con data2
    @rtype: Matriz de datos
    """
    if data2 == None:
        data2 = data1
    yr_conc = yr_concurrent(data1,data2,cons=False)   # Utiliza Fn yr_concurrent
    yrs_data,valores,label_data = datafromyrs(data1,yr_conc)   # Utiliza Fn datafromyrs
    return yrs_data,valores,label_data
    
# Matriz de datos desde lista años
def datafromyrs(data,years=None):
    """ Entrega una matriz de datos de los años solicitados
    @param data: Matriz de datos
    @param years: Lista de años solicitados
    @return: Matriz de datos de los años solicitados
    @rtype: Matriz de datos
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls', 2) # Lee sheet lost
    >>> datafromyrs(a,1951)[2][1]
    u'JAN'
    >>> datafromyrs(a,1951)[1][0][1]
    3.1000000000000001
    >>> datafromyrs(a,[1950,1951])[0]
    [1950.0, 1951.0]
    """
    # Valores
    valores = []
    # Extrae etiquetas
    label_data =  []
    for label in data[2]:
        label_data.append(label)
    # Años
    yrs_data = []
    # Caso para copy_data
    if years == None:
        years = data[0]
        allyears = True
    if type(years) != list: # Caso arg es un sólo año
        years = [years]
    for year in years:
        try:
            iyear = data[0].index(year)
        except ValueError:
            raise ValueError, "Datos requerido fuera de rango"
        # Extrae año
        yrs_data.append(data[0][iyear])
        aux = []
        for val in data[1][iyear]:
            aux.append(val)
        # Extrae fila de datos
        valores.append(aux)
    return yrs_data,valores,label_data

# Detecta si data es mensual o anual
def is_data_one_colum(data):
    """  Detecta si data es mensual o anual
    @param data: Matriz de datos
    @return: True si la matriz de datos es anual, False si no
        es anual
    @rtype: bool
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls',0) # Lee sheet mensual
    >>> b = rd_data_col(a,2)
    >>> is_data_one_colum(a)
    False
    >>> is_data_one_colum(b)
    True
    """
    return type(data[1][0]) != list

# Años concurrentes
def yr_concurrent(data1,data2,cons=False):
    """  Compara años completos concurrentes de 2 matrices de datos
    @param data1: Matriz de datos
    @param data2: Matriz de datos
    @param cons: Si es False lista de todos los años recurrentes, 
        si es True matriz de listas de años recurrentes consecutivos
    @return: Lista de años de años concurrentes de data1 y data2
    @rtype: list
    
    @note: Ejemplos
    
    >>> b = from_xls('data_test.xls',0) # Lee sheet mensual
    >>> a = from_xls('data_test.xls',3) # Lee sheet mensual1
    >>> c = from_xls('data_test.xls',1) # Lee sheet anual
    >>> yr_concurrent(a,b)
    [1950.0]
    >>> yr_concurrent(b,c)
    [1950.0, 1951.0]
    >>> yr_concurrent(b,b)
    [1950.0, 1951.0]
    >>> yr_concurrent(a,a,cons=True)
    [[1950.0], [1952.0]]
    """
    valores_tot = []
    valores = []
    # Rango de años a recorrer
    yr_init = max([min(data1[0]),min(data2[0])])
    yr_final = min([max(data1[0]),max(data2[0])])
    valores_tmp = []
    yr = yr_init
    
    while yr <= yr_final:
        # Busca que exista yr en data1 y data2
        try:
            i = data1[0].index(yr)
            j = data2[0].index(yr)
        except ValueError:
            # Pasa a la iteración siguiente
            yr += 1
            continue
        # Prueba todos los casos que data1 y data2 sean mensual o anual
        is_data_one_colum1 = is_data_one_colum(data1)
        is_data_one_colum2 = is_data_one_colum(data2)
        if is_data_one_colum1:
            if is_data_one_colum2:
                not_lost_data = data1[1][i] != '' and data2[1][j] != ''
            else:
                not_lost_data = data1[1][i] != '' and data2[1][j].count('') == 0
        # data1 tiene tiene más de 1 columna
        else:
            if is_data_one_colum2:
                not_lost_data = data1[1][i].count('') == 0 and data2[1][j] != ''
            else:
                not_lost_data = data1[1][i].count('') == 0 and data2[1][j].count('') == 0
        # Agrega años recurrentes
        if not_lost_data:
            valores_tmp.append(data1[0][i])
            valores_tot.append(data1[0][i])
        # Encontramos año no recurente
        elif valores_tmp != []:
            # Guarda el último periodo recurrente encontrado
            valores.append(valores_tmp)
            # Reinicia la búsqueda de un nuevo periodo
            valores_tmp = []
        if i == data1[0].index(yr_final) and valores_tmp != []: # Ultimo periodo recurrente
            valores.append(valores_tmp)                         # hasta el final
        yr += 1
    if cons:
        return valores
    else:
        return valores_tot

# Multiples regresiones lineales
def lin_reg(data1,data2,yr_conc=None):
    """ Calcula parámetros regresión lineal entre 2 matrices de datos
    @param data1: Matriz de datos
    @param data2: Matriz de datos
    @param yr_conc: Lista de años concurrentes que define los datos
        a utilizar en el cálculo de la regresión lineal.
        Si yr_conc=None utiliza todos los años concurrentes disponibles.
    @return: (gradient, intercept, r_value, p_value, std_err)
    @rtype: tuple
    @keyword R-squared: r_value**2
    """
    valores = []
    valores1 = []
    valores2 = []
    if yr_conc == None:
        yr_conc = yr_concurrent(data1,data2) # Utiliza Fn yr_concurrent
    for yr in yr_conc:
        rx1 = data1[0].index(yr)
        rx2 = data2[0].index(yr)
        for cx in xrange(len(data1[1][rx1])):
            valores1.append(data1[1][rx1][cx])
            valores2.append(data2[1][rx2][cx])
    gradient, intercept, r_value, p_value, std_err = stats.linregress(valores1,
                                                                      valores2)
    return [gradient, intercept, r_value, p_value, std_err]

# Busca dato anterior y posterior válido
def find_neighbors(data,iyr,cx,val=True):
    """ Busca dato anterior y posterior válido a un dato de interés.
    @param data: Matriz de datos
    @param iyr: Año del dato de interés
    @param cx: Indice de la columna del dato de interés
    @param val: Indica si se quiere los valores o la posición de los
        datos vecinos.
    @type val: bool
    @return: Si val=True retorna (ant,pos,length,place)
        Si val=False retorna (antyr,antcx,posyr,poscx,yr)
    @rtype: tuple
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls', 2) # Lee sheet lost
    >>> lind_lost_a = index_lost(a,yrx=False)
    >>> find_neighbors(a,lind_lost_a[0][0],lind_lost_a[0][1])
    Traceback (most recent call last):
        ...
    IndexError: Datos faltante extremo inferior
    >>> find_neighbors(a,lind_lost_a[3][0],lind_lost_a[3][1])
    Traceback (most recent call last):
        ...
    IndexError: Datos faltante extremo superior
    >>> c = from_xls('data_test.xls', 3) # Lee sheet mensual1
    >>> index_lost(c, yrx=False, hidecx=False)
    [[1, 3], [3, 3], [3, 4], [3, 5], [3, 6], [3, 7], [3, 8], [3, 9], [3, 10], [3, 11]]
    >>> lind_lost_c = index_lost(c,yrx=False)
    >>> find_neighbors(c,lind_lost_c[0][0],lind_lost_c[0][1])
    (4.0999999999999996, 6.0999999999999996, 2, 1)
    >>> find_neighbors(c,lind_lost_c[0][0],lind_lost_c[0][1],val=False)
    (1951.0, 2, 1951.0, 4, 1951.0)
    """
    ant = ''
    pos = ''
    antcx = cx - 1
    antiyr = iyr
    poscx = cx + 1
    posiyr = iyr
    length = 2
    place = 1
    while ant == '':
        # Caso extremo inferior
        if antcx == -1:
            if antiyr == 0:
                raise IndexError, "Datos faltante extremo inferior"
            # Requiere filas homogeneas
            antiyr -= 1
            antcx = len(data[1][antiyr]) - 1
            if data[1][antiyr][antcx] != '':
                ant = data[1][antiyr][antcx]
                break
        # Caso intermedio
        else:
            if data[1][antiyr][antcx] != '':
                ant = data[1][antiyr][antcx]
                break
        antcx = antcx - 1
        length += 1
        place += 1
    while pos == '':
        # Caso extremo superior
        if poscx == len(data[1][posiyr]):
            if posiyr == len(data[0]) - 1:
                raise IndexError, "Datos faltante extremo superior"
            # Requiere filas homogeneas
            posiyr += 1
            poscx = 0
            if data[1][posiyr][poscx] != '':
                pos = data[1][posiyr][poscx]
                break
        else:
            if data[1][posiyr][poscx] != '':
                pos = data[1][posiyr][poscx]
                break
        poscx = poscx + 1
        length += 1
    if val:
        return (ant,pos,length,place)
    else:
        return (data[0][antiyr],antcx,data[0][posiyr],poscx,data[0][iyr])

# Rellenar datos faltantes con prom datos anterior y posterior válida
def fill_data_s(data,lind_lost=None):
    """Rellenar datos faltantes con prom datos anterior y posterior válida
    @param data: Matriz de datos
    @param lind_lost: Lista de índice de datos faltantes.
        Si lind_lost=None entonces rellena todos los datos faltantes
    @return: Matriz de datos con datos rellenados
    @rtype: Matriz de datos
    
    @note: Ejemplos
    
    >>> c = from_xls('data_test.xls', 3) # Lee sheet mensual1
    >>> index_lost(c, yrx=False, hidecx=False)
    [[1, 3], [3, 3], [3, 4], [3, 5], [3, 6], [3, 7], [3, 8], [3, 9], [3, 10], [3, 11]]
    >>> c_r = fill_data_s(c)
    >>> c[1][1][3]
    ''
    >>> c_r[1][1][3]
    5.0999999999999996
    """
    yrs_data,valores,label_data = copy_data(data)
    if lind_lost == None:
        lind_lost = index_lost(data,yrx=False)
    for ind_lost in lind_lost:
        iyr = ind_lost[0]
        cx = ind_lost[1]
        try:
            # Utiliza Fn find_neighbors
            ant, pos, length, place = find_neighbors(data, iyr, cx)
        # En casos extremos no rellena datos
        except IndexError:
            pass
        # Rellena si falta un solo dato
        if length == 2:
            valores[iyr][cx] = (ant + pos) / 2
    return yrs_data,valores,label_data


# Rellenar datos faltantes con regresión lineal
def fill_data(data1,data2=None,lind_lost=None,lin_reg_param=None):
    """Rellenar datos faltantes y corrige con regresión lineal
    @param data1: Matriz de datos
    @param data2: Matriz de datos
        Si data2=None sólo rellena con prom datos anterior y posterior válida
    @param lind_lost: Lista de índice de datos faltantes.
        Si lind_lost=None entonces rellena todos los datos faltantes
    @param lin_reg_param: Parámetros de la regresión lineal
        Si lin_reg_param=None calcula los parámetros a partir de data2.
    @type lin_reg_param: tuple (gradient, intercept, r_value, p_value, std_err)
    @return: Matriz de datos con datos rellenados
    @rtype: Matriz de datos
    
    @note: Ejemplos
    
    >>> c = from_xls('data_test.xls', 3) # Lee sheet mensual1
    >>> index_lost(c, yrx=False, hidecx=False)
    [[1, 3], [3, 3], [3, 4], [3, 5], [3, 6], [3, 7], [3, 8], [3, 9], [3, 10], [3, 11]]
    >>> c_r = fill_data(c)
    >>> c[1][1][3]
    ''
    >>> c_r[1][1][3]
    5.0999999999999996
    """
    # Crea un duplicado de data 
    yrs_data,valores,label_data = copy_data(data1)
    if lind_lost == None:
        lind_lost = index_lost(data1,yrx=False)
    # Caso 1 sólo dato
    if type(lind_lost[0]) != list:
        lind_lost = [lind_lost]
        one_data = True
    if lin_reg_param == None and data2 != None:
        lin_reg_param = lin_reg(data1,data2)   # Utiliza Fn lin_reg
    for ind_lost in lind_lost:
        iyr = ind_lost[0]
        cx = ind_lost[1]
        try:
            # Utiliza Fn find_neighbors
            ant, pos, length, place = find_neighbors(data1, iyr, cx, val=True)
        # En casos extremos no rellena datos
        except IndexError:
            pass
        # Rellena datos con interpolación lineal de datos vecinos
        if length > 5 and data2 == None:
            warnings.warn("Interpolación tramo de más de 4 datos faltantes",RuntimeWarning)
        m = (pos - ant) / (length)
        yl = m * place + ant
        valores[iyr][cx] = yl
        if data2 != None and length > 2:
            try:
                ## Corrección de interpolación lineal con LR de estación data2
                antyr, antcx, posyr, poscx, yr = find_neighbors(data1,iyr,cx,val=False)
                ylr1 = data_lr(data2,[antyr, antcx],lin_reg_param)
                ylr2 = data_lr(data2,[posyr, poscx],lin_reg_param)
                ylr = data_lr(data2,[yr, cx],lin_reg_param)
                error1 = (ant - ylr1) / ant
                error3 = (pos - ylr2) / pos
                error2_ast = (error1 + error3) / 2
                yl_ast = error2_ast * yl + ylr
                yl_c = (yl_ast + yl) / 2
                # Caso correción genera caudales negativos
                if yl_c < 0:
                    pass
                else:
                    valores[iyr][cx] = yl_c
            except ValueError:
                # En caso que data_lr de un error no coorige por LR
                pass
    return yrs_data,valores,label_data

def copy_data(data):
    """ Create the copy of thr data.
    @param data: Matriz de datos original
    @return: Copia de matriz de datos
    @rtype: Matriz de datos
    
    @note: Esta función genera una copia dura de la
        matriz de datos original
    """
    yrs_data = []
    valores = []
    label_data = []
    for yr in data[0]:
        yrs_data.append(yr)
    for vals in data[1]:
        aux = []
        for val in vals:
            aux.append(val)
        valores.append(aux)
    for label in data[2]:
        label_data.append(label)
    return yrs_data,valores,label_data

# Rellenar datos faltantes con regresión lineal
# OBSOLETO
def data_lr(data2,lind_lost2,lin_reg_param):
    """ Calcula datos de una regresión lineal de estación data2
    @param data2: Matriz de datos
    @param lind_lost2: Lista de índice de datos faltantes
    @param lin_reg_param: Parámetros de la regresión lineal
    @return: Lista de datos con datos rellenados
    @rtype: list
    @todo: data_lr(data1,data2,lind_lost2,lin_reg_param)
    
    @note: Ejemplos
    
    >>> a = from_xls('data_test.xls',0) # Lee sheet mensual
    >>> b = from_xls('data_test.xls',3) # Lee sheet mensual1
    >>> lin_reg_param = [1.0, 0.0, 1.0, 7.8749999999999918e-100, 0.0]
    >>> lind_lost2 = [[1951.0, 3]]
    >>> data_lr(a,lind_lost2,lin_reg_param)
    [5.0999999999999996]
    >>> data_lr(a,[1951.0, 3],lin_reg_param)
    5.0999999999999996
    >>> data_lr(a,[[1953.0, 3]],lin_reg_param)
    Traceback (most recent call last):
    ...
    ValueError: Datos requerido fuera de rango
    """
    valores = []
    gradient = lin_reg_param[0]
    intercept = lin_reg_param[1]
    one_data = False
    if type(lind_lost2[0]) != list: # Caso 1 sólo dato
        lind_lost2 = [lind_lost2]
        one_data = True
    for ind in lind_lost2:          # lind_lost2 = index_lost(data2)
        try:
            iyr = data2[0].index(ind[0])
        except ValueError:
            raise ValueError, "Datos requerido fuera de rango"
        cx = ind[1]
        if data2[1][iyr][cx] == '':
            raise ValueError, "Faltan datos de otra estación"
        else:
            valores.append(data2[1][iyr][cx] * gradient + intercept)
    if one_data:
        return valores[0]
    else:
        return valores

# Rellenar datos faltantes con prom de datos contiguos
def data_prom(data,iyr,cx):
    """ Rellena dato con promedio de mes anterior y posterior válido
    @param data: Matriz de datos
    @param iyr: Año del dato faltante
    @param cx: Indice de la columna del dato faltante
    @return: Datos faltante calculado con prom de datos contiguos
    @rtype: float
    """
    ant, pos, length, place = find_neighbors(data, iyr, cx)
    m = (pos - ant) / (length)
    return m * place + ant

# Plotear correlacion entre 2 matrices de datos
def plot_corr_q(data1,data2,yr_conc=None,lin_reg_param=None,name_fig='fig02',title='LinReg ',path_fig=''):
    """ Plotear correlacion entre 2 matrices de datos
    @param data1: Matriz de datos
    @param data2: Matriz de datos
    @param yr_conc: Años concurrentes a plotear.
        Si yr_conc=None entonces plotea todos los años concurrentes
    @param lin_reg_param: Parámetros de la regresión lineal
        Si lin_reg_param=None calcula los parámetros a partir de data2
    @param name_fig: Nombre archivo PNG donde se guarda el ploteo
    @param title: Título del plot
    @param path_fig: Ruta de salida del plot
    @return: Archivo PNG donde se guarda el ploteo
    @rtype: bitmap file
    """
    valores1 = []
    valores2 = []
    valores_lin_reg = []
    if yr_conc == None:
        yr_conc = yr_concurrent(data1,data2) # Utiliza Fn yr_concurrent
    if lin_reg_param == None:
        lin_reg_param = lin_reg(data1,data2,yr_conc)   # Utiliza Fn lin_reg
    gradient = lin_reg_param[0]
    intercept = lin_reg_param[1]
    r_2 = lin_reg_param[2]**2
    for yr in yr_conc:
        rx1 = data1[0].index(yr)
        rx2 = data2[0].index(yr)
        for cx in xrange(len(data1[1][rx1])):
            valores1.append(data1[1][rx1][cx])
            valores2.append(data2[1][rx2][cx])
            valores_lin_reg.append(data1[1][rx1][cx] * gradient + intercept)
    plt.plot(valores1, valores2, 'g.')
    plt.plot(valores1, valores_lin_reg, 'r--')
    plt.ylabel('m3/s')
    plt.xlabel('m3/s')
    plt.legend(['Data', 'LinReg'])
    plt.title('%s %s\n m:%s, n:%s, R2:%s'%(title, name_fig, gradient, intercept, r_2))
    plt.savefig('%s%s'%(path_fig,name_fig))
    plt.close()

# Plotear datos de años con datos completos en un sólo archivo
def plot_q(data,yrs=None,name_fig='fig01',title='Caudales ',path_fig=''):
    """ Plotear caudales de años con datos completos en un sólo archivo
    @param data: Matriz de datos con caudales mensuales
    @param yrs: Lista de años a plotear
        Si yrs=None plotea todos los años
    @param name_fig: Nombre archivo PNG donde se guarda el ploteo
    @param title: Título del plot
    @param path_fig: Ruta de salida del plot
    @return: Archivo PNG donde se guarda el ploteo
    @rtype: bitmap file
    """
    if yrs == None:
        range_i = range(len(data[0]))
    else:
        range_i = []
        # Caso un solo año
        if type(yrs) != list:
            yrs = [yrs]
        for yr in yrs:
            try:
                range_i.append(data[0].index(yr))
            except ValueError:
                raise ValueError, "Año fuera de rango de datos"
    for i in range_i:
        if data[1][i].count('') == 0:
            plt.plot(range(1,len(data[2])),     # No cuenta col Year
                     data[1][i], 
                     label=str(data[0][i]))
    plt.ylabel('m3/s')
    plt.xlabel('meses')
    plt.title('%s %s'%(title, name_fig))
    plt.xticks(range(1,len(data[2])),data[2][1:])
    plt.savefig('%s%s'%(path_fig,name_fig))
    plt.close()

# Plotear volúmen anual de años con datos completos
def plot_vol(data,yrs=None,name_fig='fig02',title='Volúmenes ',path_fig='', is_data_vol=False):
    """ Plotear volúmen anual de años con datos completos
    @param data: Matriz de datos
    @param yrs: Lista de años a plotear
        Si yrs=None plotea todos los años
    @param name_fig: Nombre archivo PNG donde se guarda el ploteo
    @param title: Título del plot
    @param path_fig: Ruta de salida del plot
    @param is_data_vol: Indica si la matriz de datos es de volúmenes anuales
        Si is_data_vol=False cuando la matriz de datos es de caudales mensuales
    @return: Archivo PNG donde se guarda el ploteo
    @rtype: bitmap file
    """
    if not is_data_vol:
        data = vol_yr(data,yrs) # Fn vol_yr
    if yrs == None:
        range_i = range(len(data[0]))
    else:
        range_i = []
        if type(yrs) != list:
            yrs = [yrs]
        for yr in yrs:
            try:
                range_i.append(data[0].index(yr))
            except ValueError:
                raise ValueError, "Año fuera de rango de datos"
    plt.plot(data[0],
             data[1], 'v--',
             label=str(data[2][1]))
    
    # Poner título en unicode
    title_fig = title.decode('utf8')
    plt.ylabel('Vol[MMm3]')
    plt.xlabel(u'A\xf1os')
    plt.title('%s %s'%(title_fig, name_fig))
    #~ plt.xticks(range(len(data[0])),data[0], rotation=90)
    plt.savefig('%s%s'%(path_fig,name_fig))
    plt.close()

# Plotear datos de una columna
def plot_c(data,lcx=None,ylabel='m3/s',name_fig='fig01',title='Grafo ',path_fig=''):
    """ Plotear datos de una columna
    @param data: Matriz de datos
    @param lcx: Lista de índices de la columnas a plotear
    @param ylabel: Etiqueta del eje y
    @param name_fig: Nombre archivo PNG donde se guarda el ploteo
    @param title: Título del plot
    @param path_fig: Ruta de salida del plot
    @return: Archivo PNG donde se guarda el ploteo
    @rtype: bitmap file
    """
    if lcx == None:
        lcx = range(len(data[1][0]))
    if type(lcx) != list:
        lcx = [lcx]
    for cx in lcx:
        data_c = rd_data_col(data,cx)
        yrs_c = data_c[0]
        datos_c = data_c[1]
        label_c = data_c[2][1]
        plt.plot(yrs_c, datos_c, 'o--',label=str(label_c))
    plt.ylabel(ylabel)
    plt.xlabel(str(data_c[2][0]))
    plt.legend()
    plt.title('%s %s'%(title,name_fig))
    plt.savefig('%s%s'%(path_fig,name_fig))
    plt.close()
    
# Plotear en cada archivo datos años completos e incompletos rellenando con promedio
# datos cercanos al faltante
def plot_yr(data,years=None,name_fig='fig01',title_fig='Caudales Año',path_fig=''):
    """ Plotear en cada archivo datos años completos e incompletos 
    rellenando con promedio datos cercanos al faltante
    @param data: Matriz de datos
    @param years: Lista de años a plotear
        Si years=None plotea todos los años
    @param name_fig: Nombre archivo PNG donde se guarda el ploteo
    @param title_fig: Título del plot
    @param path_fig: Ruta de salida del plot
    @return: Archivo PNG donde se guarda el ploteo
    @rtype: bitmap file
    """
    if years == None:
        years = data[0]
    if type(years) != list: # Caso arg es un sólo año
        years = [years]
    for year in years:
        try:
            iyear = data[0].index(year)
        except ValueError:
            raise ValueError, "Año fuera de rango de datos"
        data_iyear = []
        label_iyear = []
        for cx in range(len(data[1][iyear])):
            if data[1][iyear][cx] != '':    # Meses con datos
                data_iyear.append(data[1][iyear][cx])
                label_iyear.append(data[2][cx+1])   # No cuenta col Year
            else:                           # Meses sin datos
                data_iyear.append(data_prom(data,iyear,cx)) # Fn data_prom
                label_iyear.append('XX')   # Marca dato rellenado
        plt.plot(range(len(data_iyear)), data_iyear, 'o--',label=str(data[0][iyear]))
        # Poner título en unicode
        title_fig = name_fig.decode('utf8')
        title_yr = str(int(year)).decode('utf8')
        # Transforma año para no tener problemas extension archivo por punto en float
        yr_str = str(int(year))
        plt.ylabel('m3/s')
        plt.xlabel('meses')
        plt.title('%s %s'%(title_fig, title_yr))
        plt.xticks(range(len(data_iyear)),label_iyear)
        plt.savefig('%s%s%s'%(path_fig, name_fig, yr_str))
        plt.close()
    
# Plotear datos años completos e incompletos 
# rellenado con una correlación con otra estación
def plot_yr_lr(data,years,data1,lin_reg_param,name_fig='fig01',title_fig='Caudales ',path_fig=''):
    """ Plotear en cada archivo datos años completos e incompletos 
    rellenando con con una correlación con otra estación
    @param data: Matriz de datos a plotear
    @param data1: Matriz de datos
    @param years: Lista de años a plotear
    @param lin_reg_param: Parámetros de la regresión lineal
    @param name_fig: Nombre archivo PNG donde se guarda el ploteo
    @param title_fig: Título del plot
    @param path_fig: Ruta de salida del plot
    @return: Archivo PNG donde se guarda el ploteo
    @rtype: bitmap file
    @todo: Si years=None plotea todos los años
        Si lin_reg_param=None calcula los parámetros a partir de data2.
    """
    if type(years) != list: # Caso arg es un sólo año
        years = [years]
    for year in years:            
        iyear = data[0].index(year)
        data_iyear = []
        label_iyear = []
        for cx in range(len(data[1][iyear])):
            if data[1][iyear][cx] != '':    # Meses con datos
                data_iyear.append(data[1][iyear][cx])
                label_iyear.append(data[2][cx+1])   # No cuenta col Year
            else:                           # Meses sin datos
                lr_data = data_lr(data1,[year,cx],lin_reg_param)
                data_iyear.append(lr_data) # Fn fill_data_lr
                label_iyear.append('LR')   # Marca dato rellenado
        plt.plot(range(len(data_iyear)), data_iyear, 'o--',label=str(data[0][iyear]))
        # Poner título en unicode
        title_fig = name_fig.decode('utf8')
        title_yr = str(int(year)).decode('utf8')
        # Transforma año para no tener problemas extension archivo por punto en float
        yr_str = str(int(year))
        plt.ylabel('m3/s')
        plt.xlabel('meses')
        plt.title('%s Año %s'%(title_fig, title_yr))
        plt.xticks(range(len(data_iyear)),label_iyear)
        plt.savefig('%s%s%s_lr'%(path_fig, name_fig, yr_str))
        plt.close()

# Plot años hidrológicos sin datos de una serie de matrices de datos
def plot_yr_lost(names_data,*args):
    """ Plot de años sin datos
    @param names_data: Lista con nombre de las estaciones
        correspondientes a las matrices de datos, [name1, ... ,nameN]
    @type names_data: list
    @param args: Matrices de datos, matriz_datos1, ... ,matriz_datosN
    @type args:= tuple
    @return: Archivo PNG donde se guarda el ploteo
    @rtype: bitmap file
    """
    name_fig='Años sin datos'
    path_fig=''
    
    if len(args) != len(names_data):
        raise IndexError, "largo names_data no coincide con args"
    i = 1
    for arg in args:
        yrs_lost = index_lost(arg, hidecx=True) # Utiliza Fn index_lost
        plt.plot(yrs_lost, ones(yrs_lost,i),'o') # Utiliza Fn ones
        i += 1
    # Poner título en unicode
    title_fig = name_fig.decode('utf8')
    ymin, ymax = plt.ylim()
    plt.ylim( ymin-1, ymax+1 )
    xmin, xmax = plt.xlim()
    plt.xlim( xmin-1, xmax+1 )
    plt.yticks( range(1,len(args)+1), trunc_str(names_data) ) # Utiliza Fn trunc_str
    plt.ylabel(u'Estaci\xf3n')
    plt.xlabel(u'A\xf1o')
    plt.title('%s'%title_fig)
    plt.savefig('%s%s'%(path_fig, name_fig))
    plt.close()

# Plot años hidrológicos por tipo
#TODO (Sin implementar es sólo una copia de yr_lost)
def plot_yr_type(names_data,*args):
    """ Plot de años sin datos
    names_data = [name1, ... ,nameN] 
    args = matriz_datos1, ... ,matriz_datosN
    @todo: Sin implementar
    """
    name_fig='Años sin datos'
    path_fig=''
    
    if len(args) != len(names_data):
        raise IndexError, "largo names_data no coincide con args"
    i = 1
    for arg in args:
        yrs_lost = index_lost(arg, hidecx=True) # Utiliza Fn index_lost
        plt.plot(yrs_lost, ones(yrs_lost,i),'o') # Utiliza Fn ones
        i += 1
    # Poner título en unicode
    title_fig = name_fig.decode('utf8')
    ymin, ymax = plt.ylim()
    plt.ylim( ymin-1, ymax+1 )
    xmin, xmax = plt.xlim()
    plt.xlim( xmin-1, xmax+1 )
    plt.yticks( range(1,len(args)+1), trunc_str(names_data) ) # Utiliza Fn trunc_str
    plt.ylabel(u'Estaci\xf3n')
    plt.xlabel(u'A\xf1o')
    plt.title('%s'%title_fig)
    plt.savefig('%s%s'%(path_fig, name_fig))
    plt.close()
    
# Trunca names_data
def trunc_str(names,n=6):
    """ Trunca las palabras dentro de una lista de palabras
    @param names: Lista de palabras
    @param n: Largo de palabras
    @return: Lista de nombres truncados en 6 letras
    @rtype: list
    
    @note: Ejemplos
    
    >>> names = ['Salida Laguna', 'Claro Rivadavia', 'Elqui Almendral']
    >>> trunc_str(names)
    ['Salida', 'Claro ', 'Elqui ']
    """
    aux = []
    for nam in names:
        aux.append(nam[:6])
    return aux
    
# Ones sin numpy
def ones(lista,value=1):
    """ Crea una lista de igual largo rellenando con el valor dado
    @param lista: Lista de elementos
    @param value: Valor a rellenar
    @return: Lista rellenada con valor dado
    @rtype: list
    
    @note: Ejemplos
    
    >>> ones([1,2,3],3)
    [3, 3, 3]
    >>> ones([1,2,3])
    [1, 1, 1]
    >>> ones([1,2,3,4],2)
    [2, 2, 2, 2]
    """
    aux = []
    for i in lista:
        aux.append(value)
    return aux

if __name__ == '__main__':
    import doctest
    doctest.testmod()
