from configs.config import FLUX_CAL_CONFIG
from configs.debugging_config import DEBUG_CONFIGS
from flaggers.closure_flagger import ClosureFlagger
from flaggers.r_flagger import RFlagger
from measurement_set import MeasurementSet
from flaggers.detailed_flagger import DetailedFlagger
from report import Report


def main(ms_dataset):
    measurement_set = MeasurementSet(ms_dataset)
    if not DEBUG_CONFIGS['manual_flag']:
        print "Calculating bad baselines based on angular dispersion in phases..."
        r_flagger = RFlagger(measurement_set)
        r_flagger.get_bad_baselines('flux_calibration')
        print "Calculating bad baselines based closure phases..."
        closure_flagger = ClosureFlagger(measurement_set)
        closure_flagger.get_bad_baselines()
        scan_ids = measurement_set.scan_ids_for(FLUX_CAL_CONFIG['field'])
        Report(measurement_set.antennas).generate_report(scan_ids)
        measurement_set.flag_r_and_closure_based_bad_antennas()
    print 'Detail Flagging...'
    detailed_flagger = DetailedFlagger(measurement_set)
    detailed_flagger.get_bad_antennas('flux_calibration')


