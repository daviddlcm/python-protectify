from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
from flask_cors import CORS

load_dotenv()


# Conexión a la base de datos
conexion = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    charset=os.getenv('DB_CHARSET'),
    collation=os.getenv('DB_COLLATION')
)

app = Flask(__name__,static_folder='build')

CORS(app)



@app.after_request
def after_request(response):
    response.headers['Server'] = 'My Custom Server'
    return response

@app.route("/")
def root():
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM users")
    resultados = cursor.fetchall()
    return jsonify(resultados)

@app.route("/api/<int:id>", methods=['GET'])
def probabilidad(id):
    cursor = conexion.cursor(dictionary=True)
    try:
        # Primero obtenemos los datos principales
        query = """
        SELECT 
            members.id AS member_id, 
            members.name, 
            members.last_name, 
            members.second_last_name, 
            access_key.room_id, 
            access_key.access_at, 
            access_key.exit_at 
        FROM 
            access_key 
        INNER JOIN 
            members 
        ON 
            access_key.member_id = members.id 
        WHERE 
            members.created_by = %s 
        ORDER BY 
            members.id, access_key.access_at;
        """
        cursor.execute(query, (id,))
        resultados = cursor.fetchall()

        if resultados:
            # Convertir resultados a DataFrame
            df = pd.DataFrame(resultados)
            
            # Mapeo de IDs a nombres completos
            nombres_miembros = df[['member_id', 'name', 'last_name', 'second_last_name']]
            nombres_miembros['full_name'] = nombres_miembros['name'] + ' ' + nombres_miembros['last_name'] + ' ' + nombres_miembros['second_last_name']
            nombres_miembros = nombres_miembros[['member_id', 'full_name']].drop_duplicates().set_index('member_id')['full_name'].to_dict()
            
            # Contar las entradas por miembro
            frecuencia_absoluta = df['member_id'].value_counts()
            total_registros = len(df)
            frecuencia_relativa = frecuencia_absoluta / total_registros
            frecuencia_acumulada = frecuencia_absoluta.cumsum()
            
            # Estadísticas
            media = frecuencia_absoluta.mean()
            mediana = frecuencia_absoluta.median()
            moda = frecuencia_absoluta.mode().tolist()  # Puede ser una lista si hay múltiples modas
            varianza = frecuencia_absoluta.var()
            desviacion_estandar = frecuencia_absoluta.std()

            # Convertir los IDs a nombres
            frecuencia_absoluta = frecuencia_absoluta.rename(nombres_miembros)
            frecuencia_relativa = frecuencia_relativa.rename(nombres_miembros)
            frecuencia_acumulada = frecuencia_acumulada.rename(nombres_miembros)

            # Convertir a tipos nativos de Python
            frecuencia_absoluta = frecuencia_absoluta.astype(int).to_dict()
            frecuencia_relativa = frecuencia_relativa.astype(float).to_dict()
            frecuencia_acumulada = frecuencia_acumulada.astype(int).to_dict()
            media = float(media)
            mediana = float(mediana)
            moda = [nombres_miembros.get(m) for m in moda]
            varianza = float(varianza)
            desviacion_estandar = float(desviacion_estandar)

            # Crear el resultado final con nombre del miembro como clave
            resultados_estadisticos = {}
            for nombre in nombres_miembros.values():
                resultados_estadisticos[nombre] = {
                    'frecuencia_absoluta': frecuencia_absoluta.get(nombre, 0),
                    'frecuencia_relativa': frecuencia_relativa.get(nombre, 0.0),
                    'frecuencia_acumulada': frecuencia_acumulada.get(nombre, 0)
                }
                
            resultados_estadisticos.update({
                'media': media,
                'mediana': mediana,
                'moda': moda,  # Lista de nombres para moda
                'varianza': varianza,
                'desviacion_estandar': desviacion_estandar
            })
            
            return jsonify(resultados_estadisticos)
        else:
            return jsonify({"message": "Items not found"}), 404
    except Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()

if __name__ == '__main__':
    app.run(debug=True)
