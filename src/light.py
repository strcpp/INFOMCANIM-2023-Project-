

class Light():
    def __init__(self, position, color):
        self.position = position 
        self.color = color

        # just some random values for lights
        self.Ia = 0.2 * self.color
        self.Id = 0.9 * self.color
        self.Is = 0.5 * self.color