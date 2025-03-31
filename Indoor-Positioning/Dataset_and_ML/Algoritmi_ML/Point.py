# Definizione della classe AccessPoint per rappresentare un punto di accesso con coordinate (x, y)
class AccessPoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y


# Definizione della classe ReferencePoint per rappresentare un punto di riferimento con RSSI e coordinate (x, y)
class ReferencePoint:
    def __init__(self, readings, coordinates):
        self.readings = readings  # Lista di letture RSSI
        self.coordinates = coordinates  # Array di coordinate [x, y]

