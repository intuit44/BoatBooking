#!/bin/bash
echo "Este es un archivo ejecutable en Azure Blob Storage"

# Función para calcular el área de un círculo
calcular_area_circulo() {
    local radio=$1
    local area=$(echo "scale=2; 3.14159 * $radio * $radio" | bc)
    echo "El área de un círculo con radio $radio es: $area"
}

# Llamada a la función con un radio de 5
calcular_area_circulo 5
