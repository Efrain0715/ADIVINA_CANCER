from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Cargar los datos de cáncer desde el archivo JSON
with open('cancer_data.json',encoding='utf-8') as f:
    cancer_data = json.load(f)

# Verificar o crear el archivo histórico de respuestas
if os.path.exists('respuestas_historicas.json'):
    with open('respuestas_historicas.json', 'r') as f:
        historico = json.load(f)
else:
    historico = {"historico_respuestas": []}

# Función de diagnóstico que calcula el tipo de cáncer basándose en las respuestas
def diagnosticar_cancer_adaptativo(respuestas):
    max_score = 0
    probable_cancer = "No determinado"
    current_answer_index = 0

    print("Respuestas del usuario (para diagnóstico):", respuestas)  # Depuración

    # Iterar sobre cada tipo de cáncer en la base de datos para calcular el puntaje
    for cancer in cancer_data['cancers']:
        score = 0
        print(f"Calculando para {cancer['name']}")  # Depuración: nombre del cáncer
       # cancer_responses = respuestas[:len(cancer['questions'])]  # Solo las respuestas para este tipo de cáncer
       # respuestas = respuestas[len(cancer['questions']):]  # Reducir `respuestas` para el próximo tipo de cáncer

        
        for pregunta in cancer['questions']:
            #if i < len(respuestas):  # Nos aseguramos de no exceder el índice de respuestas
            if current_answer_index < len(respuestas):
                user_response = respuestas[current_answer_index]
                peso_actual = pregunta['answer_weight'].get(user_response, 0)
                
                print(f"Pregunta: {pregunta['question']}, Respuesta: {user_response}, Peso: {peso_actual}, Score acumulado: {score}")
                score += peso_actual
                current_answer_index +=1
        # Verificar si este cáncer tiene el puntaje más alto
        print(f"Score total para {cancer['name']}: {score}")  # Depuración: puntaje final para este tipo de cáncer
        if score > max_score:
            max_score = score
            probable_cancer = cancer['name']
    
    print(f"Diagnóstico final: {probable_cancer} con puntaje: {max_score}")  # Depuración: diagnóstico final
    return probable_cancer


# Ruta para iniciar el cuestionario
@app.route('/')
def home():
    session.clear()  # Limpiar la sesión para iniciar una nueva prueba
    session['question_index'] = 0
    session['answers'] = []
    return redirect(url_for('pregunta'))

# Ruta para mostrar preguntas
@app.route('/pregunta')
def pregunta():
    question_index = session.get('question_index', 0)
    all_questions = [q for cancer in cancer_data['cancers'] for q in cancer['questions']]
    
    if question_index >= len(all_questions):
        return redirect(url_for('guardar_respuesta'))
    
    question_data = all_questions[question_index]
    return render_template('preguntas.html', pregunta=question_data)

# Ruta para procesar respuestas
@app.route('/respuesta', methods=['POST'])
def respuesta():
    respuesta_usuario = request.form['respuesta']
    session['answers'].append(respuesta_usuario)
    session['question_index'] += 1
    return redirect(url_for('pregunta'))

# Ruta para guardar respuesta final y diagnóstico
@app.route('/guardar_respuesta')
def guardar_respuesta():
    respuesta_usuario = session.get('answers', [])
    diagnostico_final = diagnosticar_cancer_adaptativo(respuesta_usuario)
    
    usuario_id = session.get('usuario_id', 'default_id')
    
    historico["historico_respuestas"].append({
        "usuario_id": usuario_id,
        "respuestas": respuesta_usuario,
        "diagnostico": diagnostico_final
    })

    with open('respuestas_historicas.json', 'w') as f:
        json.dump(historico, f, indent=4)

    return render_template('resultado.html', respuestas=respuesta_usuario, diagnostico=diagnostico_final)

@app.route('/confirmacion_respuesta', methods=['POST'])
def confirmacion_respuesta():
    confirmacion = request.form['confirmacion']

    if confirmacion == 'si':
        # Mostrar mensaje de consuelo y opción para reiniciar
        return render_template('mensaje.html')
    else:
        # Redirigir al cuestionario desde el principio
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
