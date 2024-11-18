import streamlit as st
from groq import Groq
import datetime

# Model options with short, precise descriptions
MODELOS = {
    "llama3-groq-70b-8192-tool-use-preview": "Generación de texto de alta complejidad.",
    "llama3-groq-8b-8192-tool-use-preview": "Preciso y eficiente para generación de texto.",
    "llama-3.1-70b-versatile": "Conversaciones profundas y detalladas.",
    "llama-3.1-8b-instant": "Respuestas rápidas y concisas.",
    "llama-3.2-3b-preview": "Buen equilibrio de velocidad y precisión.",
    "llama-3.2-90b-vision-preview": "Avanzado en visión e interpretación.",
    "llama-guard-3-8b": "Especializado en seguridad de respuestas.",
    "llama3-70b-8192": "Análisis y generación de texto largos.",
    "llama3-8b-8192": "Para tareas generales de conversación.",
    "mixtral-8x7b-32768": "Para contextos largos y documentos extensos."
}

# Initialize session state for messages and chat history
def inicializar_estado():
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    if "primer_mensaje" not in st.session_state:
        st.session_state.primer_mensaje = None
    if "chats_anteriores" not in st.session_state:
        st.session_state.chats_anteriores = []

# Function to create Groq client
def crear_usuario_groq():
    clave_usuario = st.secrets["CLAVE_API"]
    return Groq(api_key=clave_usuario)

# Configures the chat model and generates a response
def configurar_modelo(cliente, modelo, mensajeDeEntrada):
    mensajes_historial = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.mensajes]
    mensajes_historial.append({"role": "user", "content": mensajeDeEntrada})
    try:
        return cliente.chat.completions.create(
            model=modelo,
            messages=mensajes_historial,
            stream=True
        )
    except Exception as e:
        st.error(f"Error al generar la respuesta: {e}")
        return None

# Streams response content from the chat model
def generar_respuesta(chat_completo):
    respuesta_completa = ""
    for frase in chat_completo:
        if frase.choices[0].delta.content:
            respuesta_completa += frase.choices[0].delta.content
            yield frase.choices[0].delta.content
    return respuesta_completa

# Updates chat history in session state
def actualizar_historial(rol, contenido, avatar):
    st.session_state.mensajes.append({"role": rol, "content": contenido, "avatar": avatar})
    if rol == "user" and not st.session_state.primer_mensaje:
        st.session_state.primer_mensaje = contenido

# Displays chat history in chat interface
def mostrar_historial():
    for mensaje in st.session_state.mensajes:
        with st.chat_message(mensaje["role"], avatar=mensaje["avatar"]):
            st.markdown(f"{mensaje['content']}")

# Stores chat in session history and resets the current chat
def guardar_chat():
    if st.session_state.mensajes:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Guardar título y hora del chat
        st.session_state.chats_anteriores.append({
            "timestamp": timestamp,
            "primer_mensaje": st.session_state.primer_mensaje,
            "mensajes": st.session_state.mensajes.copy()
        })

# Configure page layout and sidebar model selection
def configurar_pagina():
    st.set_page_config("Mi chat AI")
    st.title("Chat Bot")
    st.sidebar.title("Modelos")
    modelo = st.sidebar.selectbox("Función de cada uno:", list(MODELOS.keys()), format_func=lambda x: MODELOS[x])
    return modelo

# Main function to handle chat application logic
def main():
    inicializar_estado()
    usuario = crear_usuario_groq()
    modelo_actual = configurar_pagina()

    # Mostrar el historial de chats anteriores en el sidebar
    st.sidebar.title("Chats Anteriores")
    for idx, chat in enumerate(st.session_state.chats_anteriores):
        if st.sidebar.button(f"Ver chat {idx+1} - {chat['primer_mensaje']} ({chat['timestamp']})"):
            st.session_state.mensajes = chat["mensajes"]
            st.session_state.primer_mensaje = chat["primer_mensaje"]

    # Botón para iniciar un nuevo chat
    if st.sidebar.button("Nuevo Chat"):
        guardar_chat()  # Guardar el chat actual antes de empezar uno nuevo
        st.session_state.mensajes = []  # Limpiar el historial de mensajes
        st.session_state.primer_mensaje = None  # Limpiar el primer mensaje
        st.rerun()  # Esto vuelve a cargar la página y actualiza el sidebar

    # Display chat area and input
    with st.container():
        mostrar_historial()

    mensaje = st.chat_input("Escribí tu mensaje:")
    
    if mensaje:
        # Update chat history immediately before generating a response
        actualizar_historial("user", mensaje, "😎")
        
        # Show the user message immediately
        with st.chat_message("user", avatar="😎"):
            st.markdown(mensaje)
        
        respuesta_chat_bot = ""
        
        if mensaje.lower() == "cual fue el primer mensaje que te mande?":
            respuesta_chat_bot = st.session_state.primer_mensaje or "Aún no has enviado un mensaje previo."
        else:
            respuesta_chat_bot = configurar_modelo(usuario, modelo_actual, mensaje)

        if respuesta_chat_bot:
            with st.chat_message("assistant", avatar="🤖"):
                respuesta_completa = st.write_stream(generar_respuesta(respuesta_chat_bot))
                actualizar_historial("assistant", respuesta_completa, "🤖")

if __name__ == "__main__":
    main()
