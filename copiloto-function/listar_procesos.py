# -*- coding: utf-8 -*-
import os

# Listar procesos activos
processes = os.popen('tasklist').read()
print(processes)