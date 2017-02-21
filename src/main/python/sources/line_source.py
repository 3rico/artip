from sources.target_source import TargetSource
from configs.config import ALL_CONFIGS


class LineSource(TargetSource):
    def __init__(self, measurement_set):
        super(LineSource, self).__init__(measurement_set)
        self.source_type = 'line'
        self.config = ALL_CONFIGS["target_source"][self.source_type]

    def apply_calibration(self):
        self.measurement_set.casa_runner.apply_line_calibration(self.config["calmode"])

    def reduce_data(self):
        self.measurement_set.casa_runner.extend_continuum_flags()
