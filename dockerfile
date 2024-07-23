# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /main

# Copia el archivo requirements.txt primero para aprovechar el cache de Docker
COPY requirements.txt ./

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código del proyecto al contenedor
COPY . .

# Expone el puerto en el que tu aplicación se ejecuta
EXPOSE 3034

# Comando para ejecutar la aplicación
CMD ["python", "main.py"]
