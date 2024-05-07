class DataStore:
    def __init__(self):
        self.laplacian_values = []

    def add_laplacian_value(self, frame_number, value):
        self.laplacian_values.append((frame_number, value))

    def get_laplacian_values(self):
        return self.laplacian_values

    def get_laplacian_by_percentile(self, percentile):
        if not 0 <= percentile <= 100:
            raise ValueError("Percentile must be between 0 and 100")

        percentile /= 100.0
        self.laplacian_values.sort(key=lambda x: x[1])
        index = int(len(self.laplacian_values) * percentile)
        return self.laplacian_values[index][1]
