# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_ladas():
    f = open(BASE_DIR+'/lada.txt')
    ladas = dict()
    
    for line in f:
        line = line.strip()
        name = line[:len(line)-3].strip()
        prefix = line[len(line)-3:].strip()
        # print name, prefix
        try: 
            a = ladas[prefix]
        except KeyError:
            ladas[prefix] = {
                'name': name,
                'lada' : prefix
            }

    return ladas


def load_int_ladas():
    f = open(BASE_DIR+'/lada_int.txt')
    ladas_int = dict()
    
    for line in f:
        line = line.strip().split('|')
        name = line[0].strip()
        prefix = line[1].strip()
        # print name, prefix
        try: 
            a = ladas_int[prefix]
        except KeyError:
            ladas_int[prefix] = {
                'name': name,
                'lada' : prefix
            }

    return ladas_int
