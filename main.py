import os
import qrcode
import re
import cv2
from pyzbar.pyzbar import decode
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.popup import Popup

# Verifica si la carpeta assets existe, si no, la crea
if not os.path.exists('assets'):
    os.makedirs('assets')

# Archivo donde se guardarán los códigos QR ya escaneados
registro_escaneados = "registro_escaneados.txt"

# Función para limpiar el nombre de archivo (remueve caracteres no válidos)
def sanitize_filename(filename):
    return re.sub(r'[^\w\s]', '', filename).strip().replace(" ", "_")

# Función para generar el código QR
def generate_qr_code(data, img_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(img_path)

# Función para cargar el registro de códigos escaneados
def cargar_registro():
    if not os.path.exists(registro_escaneados):
        return set()
    with open(registro_escaneados, 'r') as f:
        return set(line.strip() for line in f)

# Función para guardar un código como escaneado
def guardar_codigo_escanado(codigo):
    with open(registro_escaneados, 'a') as f:
        f.write(codigo + '\n')

# Función para escanear código QR con la cámara
def escanear_qr_con_camara(callback):
    cap = cv2.VideoCapture(0)  # Captura de video desde la cámara

    while True:
        ret, frame = cap.read()
        if not ret:
            print("No se pudo abrir la cámara")
            break
        
        # Decodificar los códigos QR en el frame
        for qr_code in decode(frame):
            qr_data = qr_code.data.decode('utf-8')
            print(f"QR Code detectado: {qr_data}")
            
            # Invocar el callback con el contenido del QR
            callback(qr_data)
            
            # Dibujar un rectángulo alrededor del código QR
            pts = qr_code.polygon
            if len(pts) == 4:
                pts = [(p.x, p.y) for p in pts]
                cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
        
        # Mostrar el frame
        cv2.imshow("Escanear Código QR", frame)

        # Presionar 'q' para salir del escaneo
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

class QRCodeApp(App):
    def build(self):
        # Configuraciones iniciales de la ventana
        Window.size = (360, 600)
        self.img_path = "assets/qr_code.png"

        # Layout principal
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Título
        title = Label(text='Generador de QR para Entrada al Evento', font_size=24)
        layout.add_widget(title)

        # Entrada de texto para el nombre de la persona
        self.person_name_input = TextInput(hint_text='Ingresa el nombre de la persona', font_size=18, size_hint_y=None, height=50)
        layout.add_widget(self.person_name_input)

        # Entrada de texto para el ID de la persona
        self.person_id_input = TextInput(hint_text='Ingresa el ID de la persona', font_size=18, size_hint_y=None, height=50)
        layout.add_widget(self.person_id_input)

        # Entrada de texto para el correo de la persona
        self.person_correo_input = TextInput(hint_text='Ingresa el correo', font_size=18, size_hint_y=None, height=50)
        layout.add_widget(self.person_correo_input)

        # Botón para generar el código QR
        generate_btn = Button(text="Generar QR", font_size=18, size_hint_y=None, height=50)
        generate_btn.bind(on_press=self.on_generate_qr)
        layout.add_widget(generate_btn)

        # Botón para escanear el código QR con la cámara
        scan_btn = Button(text="Escanear QR", font_size=18, size_hint_y=None, height=50)
        scan_btn.bind(on_press=self.on_scan_qr)
        layout.add_widget(scan_btn)

        # Imagen del código QR generado
        self.qr_image = Image(source=self.img_path)
        layout.add_widget(self.qr_image)

        return layout

    def on_generate_qr(self, instance):
        # Obtener el nombre, ID y correo ingresados
        person_name = self.person_name_input.text
        person_id = self.person_id_input.text
        person_correo = self.person_correo_input.text

        if not person_name or not person_id or not person_correo:
            # Si faltan datos, mostrar un mensaje
            popup = Popup(title='Error', content=Label(text='Por favor, completa todos los campos'), size_hint=(None, None), size=(400, 200))
            popup.open()
            return

        # Limpiar el nombre para que sea válido como nombre de archivo
        sanitized_name = sanitize_filename(person_name)

        # Crear un código QR único basado en el nombre, ID y correo
        qr_data = f'Evento: Persona: {person_name}, ID: {person_id}, Correo: {person_correo}'
        qr_img_path = f"assets/{sanitized_name}_qr_code.png"

        # Generar el código QR con la información única de la persona
        generate_qr_code(qr_data, qr_img_path)

        # Actualizar la imagen mostrada
        self.qr_image.source = qr_img_path
        self.qr_image.reload()

    def on_scan_qr(self, instance):
        # Definir el comportamiento cuando se escanee un código
        def procesar_qr(qr_data):
            codigos_escaneados = cargar_registro()
            if qr_data in codigos_escaneados:
                print(f"El código QR ya ha sido escaneado previamente: {qr_data}")
                popup = Popup(title='QR Inválido', content=Label(text='Este QR ya ha sido escaneado'), size_hint=(None, None), size=(400, 200))
                popup.open()
            else:
                print(f"Código QR válido: {qr_data}")
                guardar_codigo_escanado(qr_data)
                popup = Popup(title='QR Válido', content=Label(text='Código QR escaneado con éxito'), size_hint=(None, None), size=(400, 200))
                popup.open()

        # Escanear el código QR usando la cámara
        Clock.schedule_once(lambda dt: escanear_qr_con_camara(procesar_qr), 0)

if __name__ == '__main__':
    QRCodeApp().run()
