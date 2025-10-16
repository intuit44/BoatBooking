# -*- coding: utf-8 -*-
# coding: utf-8
import math

def calcular_radio_y_ubicacion(x1, y1, x2, y2):
    """
    Calcula el radio y la ubicación del centro de un círculo que pasa por dos puntos dados.

    :param x1: Coordenada x del primer punto
    :param y1: Coordenada y del primer punto
    :param x2: Coordenada x del segundo punto
    :param y2: Coordenada y del segundo punto
    :return: Radio del círculo y coordenadas del centro
    """
    distancia = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    radio = distancia / 2
    centro_x = (x1 + x2) / 2
    centro_y = (y1 + y2) / 2
    return radio, (centro_x, centro_y)

if __name__ == '__main__':
    punto1 = (2, 3)
    punto2 = (8, 7)
    radio, ubicacion = calcular_radio_y_ubicacion(punto1[0], punto1[1], punto2[0], punto2[1])
    print('Radio:', radio)
    print('Ubicación del centro:', ubicacion)
