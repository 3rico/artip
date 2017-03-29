from configs import config
from sources.source import Source


class BandpassCalibrator(Source):
    def __init__(self, measurement_set):
        self.source_type = 'bandpass_calibrator'
        self.config = config.ALL_CONFIGS[self.source_type]
        self.source_id = config.GLOBAL_CONFIG['bandpass_cal_fields']
        super(BandpassCalibrator, self).__init__(measurement_set)

    def calibrate(self):
        self.measurement_set.casa_runner.apply_bandpass_calibration(self.config)
