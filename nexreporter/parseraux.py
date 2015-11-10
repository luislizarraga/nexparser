# -*- coding: utf-8 -*-

from datetime import datetime, time, timedelta
from calendar import monthrange
from ladas.ladas import load_ladas, load_int_ladas
import csv
import sys
import os
import xlsxwriter

#--------------------- Global Variables -------------------

ladas = load_ladas()
ladas_int = load_int_ladas()
args = sys.argv
dir_name = ''
full = False
filename = ''
MAX_ROWS = 50
INITIAL_ROW = 0

#--------------------- Clases y funciones -----------------

class Call(object):
    """docstring for Call"""
    def __init__(self, list):
        super(Call, self).__init__()
        self.number = list[0]
        self.prefix = list[16]
        self.local = False
        self.international = False
        # self.start_date = ''
        # self.end_date = ''
        self.start_date = datetime.strptime(list[1], '%m/%d/%Y %I:%M:%S %p')
        self.end_date = datetime.strptime(list[2], '%m/%d/%Y %I:%M:%S %p')

        if list[4]:
            minutes = int(list[4].split(':')[0])
            seconds = int(list[4].split(':')[1])
            if minutes == 0: minutes = 1
            self.minutes = minutes
        else:
            self.minutes = 0

        if self.prefix == '52' or self.prefix == '52800':
            self.local = True
        elif not self.prefix.startswith('52'):
            self.international = True

        # try:
            # self.start_date = datetime.strptime(list[1], '%m/%d/%Y %H:%M:%S')
        # except:
        #     self.start_date = "N/A"

        # try:
        #     self.end_date = datetime.strptime(list[2], '%m/%d/%Y %H:%M:%S')
        # except:
        #     self.end_date = "N/A"


def parse(file):
    obj_list = list()
    file = file.split('\n')[1:]

    for line in file:
        if line == "":
            continue

        par = line[:len(line)-2]
        par = par.split(';')
        c = Call(par)
        obj_list.append(c)

    return obj_list


def aggregate(list):
    local = dict()
    cell = dict()
    otros = dict()
    mins_locales = 0
    mins_celulares = 0
    total_locales = 0
    total_celulares = 0
    mins_otros = 0
    total_otros = 0

    for c in list:
        try:
            if c.local:
                call = local[c.number]
            elif c.international:
                call = otros[c.number]
            else:
                call = cell[c.number]
        except:
            call = [0,0,0,'?'] # [número,minutos,sesiones,fecha]

        call[0] = c.number
        call[3] = c.start_date

        if c.prefix == "52":
            call[2] = call[2] + 1
            call[1] = call[1] + c.minutes
            call[0] = c.number[2:]
            local[c.number] = call
            mins_locales = mins_locales+c.minutes
            total_locales = total_locales + 1
        elif c.prefix == "521":
            call[1] = call[1] + c.minutes
            call[2] = call[2] + 1
            call[0] = c.number[3:]
            cell[c.number] = call
            mins_celulares = mins_celulares+c.minutes
            total_celulares = total_celulares + 1
        elif c.prefix == "52800":
            call[2] = call[2] + 1
            call[1] = call[1] + c.minutes
            # call[0] = c.number
            local[c.number] = call
            mins_locales = mins_locales+c.minutes
            total_locales = total_locales + 1
        else:
            call[2] = call[2] + 1
            call[1] = call[1] + c.minutes
            # call[0] = c.number
            otros[c.number] = call
            mins_otros = mins_otros+c.minutes
            total_otros = total_otros + 1

    return [
        local,
        cell,
        total_locales,
        mins_locales,
        total_celulares,
        mins_celulares,
        otros,
        total_otros,
        mins_otros
    ]


def set_lada_name(calls,ladas,other=False,ladas_int=dict()):
    result = []
    for c in calls:
        c = calls[c]
        number = c[0]
        formatted_number = number
        
        if not other:
            if number.startswith(('55','33','81')):
                c.append(ladas[number[:2]]['name'])
                formatted_number = '('+formatted_number[:2]+') '\
                    + formatted_number[2:6] + '-' + formatted_number[6:]
            elif number.startswith('52800'):
                c.append('Mexico 800')
                formatted_number = '01' + formatted_number[2:]
                formatted_number = '('+formatted_number[:5]+') '\
                    + formatted_number[5:8] + '-' + formatted_number[8:]
            else:
                c.append(ladas[number[:3]]['name'])
                formatted_number = '('+formatted_number[:3]+') '\
                    + formatted_number[3:6] + '-' + formatted_number[6:]
        else:
            try :
                c.append(ladas_int[number[:2]]['name'])
            except:
                c.append('Otros')
            formatted_number = '('+formatted_number[:2]+') '\
                    + formatted_number[2:7] + '-' + formatted_number[7:]

        c[0] = formatted_number
        result.append([c[0],'','','',c[4],'',c[1],c[2],c[3]])

    return result


def get_month_name(n):
    if n == 1:
        return 'Enero'
    elif n == 2:
        return 'Febrero'
    elif n == 3:
        return 'Marzo'
    elif n == 4:
        return 'Abril'
    elif n == 5:
        return 'Mayo'
    elif n == 6:
        return 'Junio'
    elif n == 7:
        return 'Julio'
    elif n == 8:
        return 'Agosto'
    elif n == 9:
        return 'Septiembre'
    elif n == 10:
        return 'Octubre'
    elif n == 11:
        return 'Noviembre'
    elif n == 12:
        return 'Diciembre'
    else:
        return 'N/A'


def make_cut(parsed, dir_name, start, end, extra_info):
    aux_list = []
    # add = False
    month = start.month
    interval = start.strftime('%d ')\
        + get_month_name(start.month) + start.strftime(' %y')\
        + ' al ' + (end-timedelta(days=1)).strftime('%d')\
        + get_month_name(end.month) + end.strftime(' %y')

    for c in parsed:
        # if c.start_date.day == 8 and c.start_date.month != month:
        #     start = c.start_date
        #     weekday,days = monthrange(start.year, start.month)
        #     end = c.start_date.date() + timedelta(days=days)
        #     end = datetime.combine(end,time(0,0,0,0))
        #     print start, end
            
        #     if add:
        #         result = aggregate(aux_list)
        #         save_data(result, get_month_name(month), dir_name)
        #         aux_list = []
        #         month = start.month
        #     else:
        #         add = True
        #         month = start.month

        if c.start_date >= start and c.start_date < end:
            aux_list.append(c)

    result = aggregate(aux_list)
    save_data(result, interval, dir_name, extra_info)

# en month esta el intervalo
def write_excel(data, dir_name, month, extra_info):
    workbook = xlsxwriter.Workbook(dir_name, {'in_memory': True})
    worksheet = workbook.add_worksheet()
    format1 = workbook.add_format()
    format1.set_bg_color('#1f497d')
    format2 = workbook.add_format({'font_size': 16})
    format3 = workbook.add_format({'font_name': 'Calibri', 'font_size': 10})
    format4 = workbook.add_format({'font_name': 'Calibri', 'font_size': 11})
    format5 = workbook.add_format({'font_size': 8})
    row = INITIAL_ROW
    page_breaks = []

    #------------- Configuración longitud de columnas ----------------
    worksheet.set_column(0,0, 1)
    worksheet.set_column(1,1, .2)
    worksheet.set_column(2,2, 12)
    worksheet.set_column(5,5, 12)
    worksheet.set_column(3,3, 7)
    worksheet.set_column(4,4, 7)
    worksheet.set_column(6,6, 13)
    worksheet.set_column(9,9, 11)
    worksheet.set_column(8,8, 9)
    

    #Poner imagen
    # worksheet.insert_image(row,2, 'static/img/logo_nextor.jpg')
    worksheet.set_header('&L&G', {'image_left': 'static/img/logo_nextor.jpg'})
    worksheet.set_footer('&C&10NZXT TELECOMUNICACIONES DE MEXICO S.A. DE C.V. |'\
        +' Leibnitz 47 - 105 Col. Anzures, Mexico DF 11590 |'\
        +' www.nextortelecom.com | (55, 81 y 33) 1454-0020')
    ##------------- Imagen y nombre del cliente y factura ----------------
    row = row+1
    worksheet.write(row,6, extra_info[0][0])
    worksheet.write(row+1,6, extra_info[0][1])
    row = row+2

    #------------- Header La Nubesota ----------------
    worksheet.set_row(row,25)
    worksheet.set_row(row+1,1.95)
    worksheet.write(row,1, '',format1)
    worksheet.write(row,2, 'La Nubesota', format2)
    worksheet.write(row,5, 'Intervalo')
    worksheet.write(row,7, 'Total')
    worksheet.write(row,9, 'Costo Intervalo')
    worksheet.write(row+1,1, '', format1)
    worksheet.write(row+1,2, '', format1)
    worksheet.write(row+1,3, '', format1)
    worksheet.write(row+1,4, '', format1)
    worksheet.write(row+1,5, '', format1)
    worksheet.write(row+1,6, '', format1)
    worksheet.write(row+1,7, '', format1)
    worksheet.write(row+1,8, '', format1)
    worksheet.write(row+1,9, '', format1)


    #------------- Info La Nubesota ----------------
    row = row+2
    for x in xrange(1,len(extra_info)):
        worksheet.write(row,2, extra_info[x][0], format5)
        worksheet.write(row,5, month, format5)
        worksheet.write(row,7, extra_info[x][1], format5)
        worksheet.write(row,9, extra_info[x][2], format4)
        row = row+1


    #------------- Separador La Nubesota ----------------
    # row = row+3
    worksheet.set_row(row,1.95)
    worksheet.write(row,1, '', format1)
    worksheet.write(row,2, '', format1)
    worksheet.write(row,3, '', format1)
    worksheet.write(row,4, '', format1)
    worksheet.write(row,5, '', format1)
    worksheet.write(row,6, '', format1)
    worksheet.write(row,7, '', format1)
    worksheet.write(row,8, '', format1)
    worksheet.write(row,9, '', format1)

    worksheet.write(row+1,7, 'Total', format4)
    row = row+3


    #------------- Header General Salidas ----------------
    worksheet.set_row(row,25)
    worksheet.set_row(row+1,1.95)
    worksheet.write(row,1, '',format1)
    worksheet.write(row,2, 'General Salidas', format2)
    worksheet.write(row,5, 'Minutos')
    worksheet.write(row,6, 'Sesiones')
    worksheet.write(row,7, 'Incluidas')
    worksheet.write(row,9, 'Total a pagar')
    worksheet.write(row+1,1, '', format1)
    worksheet.write(row+1,2, '', format1)
    worksheet.write(row+1,3, '', format1)
    worksheet.write(row+1,4, '', format1)
    worksheet.write(row+1,5, '', format1)
    worksheet.write(row+1,6, '', format1)
    worksheet.write(row+1,7, '', format1)
    worksheet.write(row+1,8, '', format1)
    worksheet.write(row+1,9, '', format1)

    #------------- Info General Salidas ----------------
    row = row+2
    worksheet.write(row,2, 'Mexico Fijo', format4)
    worksheet.write(row+1,2, 'Mexico Cel', format4)
    worksheet.write(row+2,2, 'Internacional', format4)
    worksheet.write(row,5, data[3], format4)
    worksheet.write(row+1,5, data[5], format4)
    worksheet.write(row+2,5, data[8], format4)
    worksheet.write(row,6, data[2], format4)
    worksheet.write(row+1,6, data[4], format4)
    worksheet.write(row+2,6, data[7], format4)

    #------------- Separador General Salidas ----------------
    row = row+3
    worksheet.set_row(row,1.95)
    worksheet.write(row,1, '', format1)
    worksheet.write(row,2, '', format1)
    worksheet.write(row,3, '', format1)
    worksheet.write(row,4, '', format1)
    worksheet.write(row,5, '', format1)
    worksheet.write(row,6, '', format1)
    worksheet.write(row,7, '', format1)
    worksheet.write(row,8, '', format1)
    worksheet.write(row,9, '', format1)

    worksheet.write(row+1,7, 'Total', format4)
    row = row+3

    #------------- Info Llamadas Mexico Fijo ----------------
    worksheet.set_row(row,25)
    worksheet.set_row(row+1,1.95)
    worksheet.write(row,1, '',format1)
    worksheet.write(row,2, 'General Salidas Mexico Fijo', format2)
    worksheet.write(row,6, 'Destino')
    # worksheet.write(row,8, 'Minutos')
    worksheet.write(row,9, 'Llamadas')
    worksheet.write(row+1,1, '', format1)
    worksheet.write(row+1,2, '', format1)
    worksheet.write(row+1,3, '', format1)
    worksheet.write(row+1,4, '', format1)
    worksheet.write(row+1,5, '', format1)
    worksheet.write(row+1,6, '', format1)
    worksheet.write(row+1,7, '', format1)
    worksheet.write(row+1,8, '', format1)
    worksheet.write(row+1,9, '', format1)
    row = row+2

    n = row
    first = True
    local = data[0]
    rows = 0
    for l in sorted(local.items(), key=lambda e: e[1][2], reverse=True):
    # for l in local:
        # if first and n == 53:
        #     rows = 2
        #     first = False
        #     page_breaks.append(n)
        #     worksheet.set_row(n,25)
        #     worksheet.set_row(n+1,1.95)
        #     worksheet.write(n,1, '',format1)
        #     worksheet.write(n,2, 'General Salidas Mexico Fijo', format2)
        #     worksheet.write(n,6, 'Destino')
        #     # worksheet.write(n,8, 'Minutos')
        #     worksheet.write(n,9, 'Llamadas')
        #     worksheet.write(n+1,1, '', format1)
        #     worksheet.write(n+1,2, '', format1)
        #     worksheet.write(n+1,3, '', format1)
        #     worksheet.write(n+1,4, '', format1)
        #     worksheet.write(n+1,5, '', format1)
        #     worksheet.write(n+1,6, '', format1)
        #     worksheet.write(n+1,7, '', format1)
        #     worksheet.write(n+1,8, '', format1)
        #     worksheet.write(n+1,9, '', format1)
        #     n = n+2

        # if rows%MAX_ROWS == 0 and not first:
        #     rows = 2
        #     page_breaks.append(n)
        #     worksheet.set_row(n,25)
        #     worksheet.set_row(n+1,1.95)
        #     worksheet.write(n,1, '',format1)
        #     worksheet.write(n,2, 'General Salidas Mexico Fijo', format2)
        #     worksheet.write(n,6, 'Destino')
        #     # worksheet.write(n,8, 'Minutos')
        #     worksheet.write(n,9, 'Llamadas')
        #     worksheet.write(n+1,1, '', format1)
        #     worksheet.write(n+1,2, '', format1)
        #     worksheet.write(n+1,3, '', format1)
        #     worksheet.write(n+1,4, '', format1)
        #     worksheet.write(n+1,5, '', format1)
        #     worksheet.write(n+1,6, '', format1)
        #     worksheet.write(n+1,7, '', format1)
        #     worksheet.write(n+1,8, '', format1)
        #     worksheet.write(n+1,9, '', format1)
        #     n = n+2
        
        worksheet.write(n,2,l[1][0],format3)
        worksheet.write(n,6,l[1][4],format3)
        # worksheet.write(n,8,local[l][2],format3)
        worksheet.write(n,9,l[1][2],format3)
        n = n+1
        rows = rows+1

    
    #------------- Info Llamadas Mexico Celular ----------------
    
    worksheet.set_row(n,25)
    worksheet.set_row(n+1,1.95)
    worksheet.write(n,1, '',format1)
    worksheet.write(n,2, 'General Salidas Mexico Celular', format2)
    worksheet.write(n,6, 'Destino')
    worksheet.write(n,8, 'Minutos')
    worksheet.write(n,9, 'Llamadas')
    worksheet.write(n+1,1, '', format1)
    worksheet.write(n+1,2, '', format1)
    worksheet.write(n+1,3, '', format1)
    worksheet.write(n+1,4, '', format1)
    worksheet.write(n+1,5, '', format1)
    worksheet.write(n+1,6, '', format1)
    worksheet.write(n+1,7, '', format1)
    worksheet.write(n+1,8, '', format1)
    worksheet.write(n+1,9, '', format1)

    n = n+2
    cell = data[1]
    rows = 0
    for l in sorted(cell.items(), key=lambda e: e[1][1], reverse=True):
    # for l in cell:
        # if rows%MAX_ROWS == 0:
        #     rows = 2
        #     page_breaks.append(n)
        #     worksheet.set_row(n,25)
        #     worksheet.set_row(n+1,1.95)
        #     worksheet.write(n,1, '',format1)
        #     worksheet.write(n,2, 'General Salidas Mexico Celular', format2)
        #     worksheet.write(n,6, 'Destino')
        #     worksheet.write(n,8, 'Minutos')
        #     worksheet.write(n,9, 'Llamadas')
        #     worksheet.write(n+1,1, '', format1)
        #     worksheet.write(n+1,2, '', format1)
        #     worksheet.write(n+1,3, '', format1)
        #     worksheet.write(n+1,4, '', format1)
        #     worksheet.write(n+1,5, '', format1)
        #     worksheet.write(n+1,6, '', format1)
        #     worksheet.write(n+1,7, '', format1)
        #     worksheet.write(n+1,8, '', format1)
        #     worksheet.write(n+1,9, '', format1)
        #     n = n+2

        # worksheet.write(n,2,cell[l][0],format3)
        worksheet.write(n,2,l[1][0],format3)
        worksheet.write(n,6,l[1][4],format3)
        worksheet.write(n,8,l[1][1],format3)
        worksheet.write(n,9,l[1][2],format3)
        n = n+1
        rows = rows+1

    #------------- Info Llamadas Mexico Celular ----------------
    
    worksheet.set_row(n,25)
    worksheet.set_row(n+1,1.95)
    worksheet.write(n,1, '',format1)
    worksheet.write(n,2, 'General Salidas Internacional', format2)
    worksheet.write(n,6, 'Destino')
    worksheet.write(n,8, 'Minutos')
    worksheet.write(n,9, 'Llamadas')
    worksheet.write(n+1,1, '', format1)
    worksheet.write(n+1,2, '', format1)
    worksheet.write(n+1,3, '', format1)
    worksheet.write(n+1,4, '', format1)
    worksheet.write(n+1,5, '', format1)
    worksheet.write(n+1,6, '', format1)
    worksheet.write(n+1,7, '', format1)
    worksheet.write(n+1,8, '', format1)
    worksheet.write(n+1,9, '', format1)

    n = n+2
    others = data[6]
    rows = 0
    for l in sorted(others.items(), key=lambda e: e[1][1], reverse=True):
    # for l in cell:
        # if rows%MAX_ROWS == 0:
        #     rows = 2
        #     page_breaks.append(n)
        #     worksheet.set_row(n,25)
        #     worksheet.set_row(n+1,1.95)
        #     worksheet.write(n,1, '',format1)
        #     worksheet.write(n,2, 'General Salidas Mexico Celular', format2)
        #     worksheet.write(n,6, 'Destino')
        #     worksheet.write(n,8, 'Minutos')
        #     worksheet.write(n,9, 'Llamadas')
        #     worksheet.write(n+1,1, '', format1)
        #     worksheet.write(n+1,2, '', format1)
        #     worksheet.write(n+1,3, '', format1)
        #     worksheet.write(n+1,4, '', format1)
        #     worksheet.write(n+1,5, '', format1)
        #     worksheet.write(n+1,6, '', format1)
        #     worksheet.write(n+1,7, '', format1)
        #     worksheet.write(n+1,8, '', format1)
        #     worksheet.write(n+1,9, '', format1)
        #     n = n+2

        # worksheet.write(n,2,cell[l][0],format3)
        worksheet.write(n,2,l[1][0],format3)
        worksheet.write(n,6,l[1][4],format3)
        worksheet.write(n,8,l[1][1],format3)
        worksheet.write(n,9,l[1][2],format3)
        n = n+1
        rows = rows+1

    worksheet.set_v_pagebreaks(page_breaks)
    workbook.close()


def save_data(data, month, dir_name, extra_info):
    local = data[0]
    cell = data[1]
    others = data[6]
    local = set_lada_name(local,ladas)
    cell = set_lada_name(cell,ladas)
    others = set_lada_name(others,ladas,True, ladas_int)
    data_aux = [local,cell] + data[2:5] + [others] + data[7:]
    write_excel(data, dir_name, month, extra_info)
