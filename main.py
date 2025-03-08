from machine import Pin, SoftI2C, Timer
import mpu6050
import ubluetooth
import math
import time

# Configuración de I2C con depuración
def init_i2c():
    try:
        print("Inicializando I2C...")
        i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
        
        # Escanear dispositivos I2C
        devices = i2c.scan()
        print(f"Dispositivos I2C detectados: {devices}")
        
        return i2c
    except Exception as e:
        print("Error crítico de inicialización I2C")
        print(str(e))
        return None

# Inicializar I2C
i2c = init_i2c()

if i2c is None:
    print("Inicialización de I2C fallida")
    # Función de error simulada para evitar detener el script
    def error_handler():
        while True:
            print("Error de inicialización. Reinicie el dispositivo.")
            time.sleep(1)
else:
    # Inicializar MPU6050 con más depuración
    try:
        print("Inicializando MPU6050...")
        mpu = mpu6050.accel(i2c)
        print("MPU6050 inicializado correctamente")
    except Exception as e:
        print("Error al inicializar MPU6050")
        print(str(e))
        mpu = None

# Clase BLE modificada para más depuración
class BLE:
    def __init__(self, mpu):
        print("Inicializando Bluetooth...")
        self.mpu = mpu
        self.ble = ubluetooth.BLE()
        self.ble.active(True)
        self.is_connected = False
        self.connection_attempts = 0
        
        try:
            self.register()
            self.advertiser()
            print("Bluetooth inicializado correctamente")
        except Exception as e:
            print("Error al inicializar Bluetooth")
            print(str(e))
    
    def register(self):
        print("Registrando servicios Bluetooth...")
        NUS_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
        TX_UUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
        BLE_NUS = ubluetooth.UUID(NUS_UUID)
        BLE_TX = (ubluetooth.UUID(TX_UUID), ubluetooth.FLAG_NOTIFY)
        BLE_UART = (BLE_NUS, (BLE_TX,))
        SERVICES = (BLE_UART, )
        
        try:
            ((self.tx,), ) = self.ble.gatts_register_services(SERVICES)
            print("Servicios Bluetooth registrados")
        except Exception as e:
            print("Error al registrar servicios Bluetooth")
            print(str(e))
        
        self.ble.irq(self.ble_irq)
    
    def ble_irq(self, event, data):
        print(f"Evento Bluetooth: {event}")
        if event == 1:  # _IRQ_CENTRAL_CONNECT
            self.is_connected = True
            self.connection_attempts += 1
            print(f"Dispositivo conectado (Intento {self.connection_attempts})")
        elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
            self.is_connected = False
            print("Dispositivo desconectado")
            self.advertiser()
    
    def send(self, data):
        try:
            if not self.is_connected:
                print("No hay conexión Bluetooth")
                return False
            
            # Convertir a bytes si es necesario
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            self.ble.gatts_notify(0, self.tx, data + b'\n')
            return True
        except Exception as e:
            print(f"Error al enviar por BLE: {e}")
            return False
    
    def advertiser(self):
        print("Anunciando dispositivo Bluetooth...")
        name = bytes("ESP32POS", 'UTF-8')
        adv_data = bytearray(b'\x02\x01\x06') + bytearray((len(name) + 1, 0x09)) + name
        
        try:
            self.ble.gap_advertise(100, adv_data)
            print("Anunciando ESP32 por Bluetooth...")
        except Exception as e:
            print("Error al anunciar Bluetooth")
            print(str(e))

# Inicializar solo si I2C y MPU están OK
if i2c and mpu:
    ble = BLE(mpu)
    print("Sistema inicializado")

    # Función para enviar datos con más depuración
    def enviar_datos(t):
        try:
            # Obtener valores del sensor
            datos = mpu.get_values()
            
            # Convertir valores de aceleración
            acc_x = round(datos["AcX"] / 16384.0, 2)
            acc_y = round(datos["AcY"] / 16384.0, 2)
            acc_z = round(datos["AcZ"] / 16384.0, 2)
            
            # Valores de giroscopio
            gyr_x = round(datos["GyX"] / 131.0, 2)
            gyr_y = round(datos["GyY"] / 131.0, 2)
            gyr_z = round(datos["GyZ"] / 131.0, 2)

            # Formatear datos para envío
            data_str = f"{acc_x},{acc_y},{acc_z},{gyr_x},{gyr_y},{gyr_z}"
            
            # Depuración de datos
            print(f"Datos a enviar: {data_str}")
            
            # Intentar enviar
            if ble.send(data_str):
                print("Datos enviados correctamente")
            else:
                print("Fallo al enviar datos")
        
        except Exception as e:
            print(f"Error en enviar_datos: {e}")

    # Configurar timer con más información
    try:
        timer = Timer(0)
        timer.init(period=20, mode=Timer.PERIODIC, callback=enviar_datos)
        print("Timer iniciado, enviando datos cada 500ms")
    except Exception as e:
        print(f"Error al iniciar timer: {e}")
else:
    print("No se pudo inicializar sistema completo")