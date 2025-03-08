import machine
from time import sleep


class accel(): 
    def __init__(self, i2c, addr=0x68):
        self.iic = i2c
        self.addr = addr
        # Forzar reinicio del sensor
        self.iic.writeto_mem(self.addr, 0x6B, b'\x80')  # Enviar comando de reset
        sleep(0.1)  # Esperar a que se reinicie
        # Sacarlo del modo de suspensión
        self.iic.writeto_mem(self.addr, 0x6B, b'\x00')
        sleep(0.1)
        
        # Configurar rango de aceleración y giroscopio
        self.iic.writeto_mem(self.addr, 0x1C, b'\x00')  # Rango de ±2g
        self.iic.writeto_mem(self.addr, 0x1B, b'\x00')  # Rango de giroscopio ±250°/s
        
        # Inicializar variables de calibración
        self.accel_offset = {'x': 0, 'y': 0, 'z': 0}
        self.gyro_offset = {'x': 0, 'y': 0, 'z': 0}

    def calibrate(self, samples=1000):
        """
        Función de calibración para calcular offsets
        """
        print("Calibrando MPU6050... Por favor, mantenga el sensor inmóvil")
        
        # Inicializar acumuladores
        accel_x_sum, accel_y_sum, accel_z_sum = 0, 0, 0
        gyro_x_sum, gyro_y_sum, gyro_z_sum = 0, 0, 0

        for _ in range(samples):
            raw_values = self.get_values()
            
            # Sumar valores de acelerómetro
            accel_x_sum += raw_values['AcX']
            accel_y_sum += raw_values['AcY']
            accel_z_sum += raw_values['AcZ'] - 16384  # Ajustar por gravedad (1g = 16384 en ±2g)
            
            # Sumar valores de giroscopio
            gyro_x_sum += raw_values['GyX']
            gyro_y_sum += raw_values['GyY']
            gyro_z_sum += raw_values['GyZ']
            
            sleep(0.01)

        # Calcular promedios (offsets)
        self.accel_offset['x'] = accel_x_sum / samples
        self.accel_offset['y'] = accel_y_sum / samples
        self.accel_offset['z'] = accel_z_sum / samples
        
        self.gyro_offset['x'] = gyro_x_sum / samples
        self.gyro_offset['y'] = gyro_y_sum / samples
        self.gyro_offset['z'] = gyro_z_sum / samples

        print("Calibración completada:")
        print(f"Accel Offsets: X={self.accel_offset['x']:.2f}, Y={self.accel_offset['y']:.2f}, Z={self.accel_offset['z']:.2f}")
        print(f"Gyro Offsets: X={self.gyro_offset['x']:.2f}, Y={self.gyro_offset['y']:.2f}, Z={self.gyro_offset['z']:.2f}")

        return self.accel_offset, self.gyro_offset

    def get_raw_values(self):
        self.iic.start()
        a = self.iic.readfrom_mem(self.addr, 0x3B, 14)
        self.iic.stop()
        return a

    def get_ints(self):
        b = self.get_raw_values()
        return [i for i in b]

    def bytes_toint(self, firstbyte, secondbyte):
        if not firstbyte & 0x80:
            return firstbyte << 8 | secondbyte
        return - (((firstbyte ^ 255) << 8) | (secondbyte ^ 255) + 1)

    def get_values(self):
        """
        Método modificado para aplicar calibración
        """
        sleep(0.1)  # Pequeño retraso para evitar lecturas congeladas
        raw_ints = self.get_raw_values()
        
        vals = {}
        vals["Tmp"] = ((raw_ints[6] << 8) | raw_ints[7]) / 340.0 + 36.53
        
        # Aplicar calibración a los valores de acelerómetro
        vals["AcX"] = self.bytes_toint(raw_ints[0], raw_ints[1]) - self.accel_offset['x']
        vals["AcY"] = self.bytes_toint(raw_ints[2], raw_ints[3]) - self.accel_offset['y']
        vals["AcZ"] = self.bytes_toint(raw_ints[4], raw_ints[5]) - self.accel_offset['z']
        
        # Valores de giroscopio
        vals["GyX"] = self.bytes_toint(raw_ints[8], raw_ints[9]) - self.gyro_offset['x']
        vals["GyY"] = self.bytes_toint(raw_ints[10], raw_ints[11]) - self.gyro_offset['y']
        vals["GyZ"] = self.bytes_toint(raw_ints[12], raw_ints[13]) - self.gyro_offset['z']
    
        return vals

    def val_test(self):  # SOLO PARA PRUEBAS
        while True:
            print(self.get_values())
            sleep(0.05)
