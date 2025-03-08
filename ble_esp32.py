import asyncio
from bleak import BleakClient
import matplotlib.pyplot as plt
from collections import deque

# UUIDs del servicio UART BLE
CHARACTERISTIC_UUID_NOTIFY = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
CHARACTERISTIC_UUID_WRITE = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"

# Dirección MAC del ESP32 (ajústala si es diferente)
ESP32_ADDRESS = "3C:8A:1F:A8:01:86"

# Almacenamiento de datos para el gráfico
data_ax = deque(maxlen=100)
data_ay = deque(maxlen=100)
data_az = deque(maxlen=100)

# Función para actualizar el gráfico
def update_plot():
    plt.clf()
    
    plt.plot(data_ax, label='Aceleración X')
    plt.plot(data_ay, label='Aceleración Y')
    plt.plot(data_az, label='Aceleración Z')
    plt.legend(loc='upper right')
    plt.title('Aceleración desde ESP32 (Ejes X, Y y Z)')
    
    plt.pause(0.01)  # Actualización aún más rápida

# Callback para recibir datos async
def notification_handler(sender, data):
    try:
        decoded_data = data.decode('utf-8').strip().split(',')
        if len(decoded_data) >= 6:
            ax, ay, az, gx, gy, gz = map(float, decoded_data[:6])
            data_ax.append(ax)
            data_ay.append(ay)
            data_az.append(az)
            update_plot()
    except Exception as e:
        print(f"Error al procesar datos: {e}")

# Función para conectar y recibir datos
async def main():
    print("Buscando ESP32...")
    async with BleakClient(ESP32_ADDRESS) as client:
        print(f"Conectado a {ESP32_ADDRESS}")

        # Suscribirse a las notificaciones
        await client.start_notify(CHARACTERISTIC_UUID_NOTIFY, notification_handler)

        print("Recibiendo datos... Presiona Ctrl+C para detener.")
        plt.ion()  # Modo interactivo de matplotlib
        plt.show()

        # Mantener la conexión abierta
        try:
            while True:
                await asyncio.sleep(0.01)  # Actualización aún más rápida
        except KeyboardInterrupt:
            print("Desconectando...")
            await client.stop_notify(CHARACTERISTIC_UUID_NOTIFY)

asyncio.run(main())