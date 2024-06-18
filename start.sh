#!/bin/bash

# Activar el entorno virtual
source venv/bin/activate

# Establecer PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Iniciar la aplicación con uvicorn
uvicorn app.main:app --reload
