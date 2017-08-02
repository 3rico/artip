from configs import config
from casa.flag_reasons import BAD_ANTENNA_TIME, BAD_BASELINE_TIME
import os
import platform
import subprocess
import casac
from logger import logger
from terminal_color import Color
from helpers import format_spw_with_channels


class CasaRunner:
    def __init__(self, dataset_path, output_path):
        self._output_path = output_path
        self._dataset_path = dataset_path

    def flagdata(self, reasons, output_path=None):
        if not output_path: output_path = self._output_path
        logger.info(Color.HEADER + "Flagging " + reasons + Color.ENDC)
        script_path = 'casa_scripts/flag.py'
        flag_file = output_path + "/flags.txt"
        script_parameters = "{0} {1} {2}".format(self._dataset_path, flag_file, reasons)
        self._run(script_path, script_parameters)

    def quack(self):
        logger.info(Color.HEADER + "Running quack..." + Color.ENDC)
        script_path = 'casa_scripts/quack.py'
        self._run(script_path)

    def apply_flux_calibration(self, source_config, run_count):
        logger_message = "Applying Flux Calibration"
        if run_count > 1: logger_message += " with bandpass"

        logger.info(Color.HEADER + logger_message + Color.ENDC)
        script_path = 'casa_scripts/flux_calibration.py'
        fields = ",".join(map(str, source_config['fields']))
        refant = config.GLOBAL_CONFIG['refant']
        minsnr = source_config['minsnr']
        spw = format_spw_with_channels(config.GLOBAL_CONFIG['spw_range'], source_config['channel'])
        script_parameters = "{0} {1} {2} {3} {4} {5} {6}".format(run_count, self._dataset_path,
                                                                 self._output_path,
                                                                 fields, refant, spw, minsnr)
        self._run(script_path, script_parameters)

    def apply_bandpass_calibration(self, source_config):
        logger.info(Color.HEADER + "Running Bandpass Calibration..." + Color.ENDC)
        script_path = 'casa_scripts/bandpass_calibration.py'
        fields = ",".join(map(str, source_config['fields']))
        refant = config.GLOBAL_CONFIG['refant']
        minsnr = source_config['minsnr']
        script_parameters = "{0} {1} {2} {3} {4}".format(self._dataset_path, self._output_path, fields, refant, minsnr)

        self._run(script_path, script_parameters)

    def apply_phase_calibration(self, flux_cal_field, source_config):
        logger.info(Color.HEADER + "Applying Phase Calibration..." + Color.ENDC)
        script_path = 'casa_scripts/phase_calibration.py'
        phase_cal_fields = ",".join(map(str, source_config['fields']))
        refant = config.GLOBAL_CONFIG['refant']
        minsnr = source_config['minsnr']
        spw = format_spw_with_channels(config.GLOBAL_CONFIG['spw_range'], source_config['channels_to_avg'])
        script_parameters = "{0} {1} {2} {3} {4} {5} {6}".format(self._dataset_path, self._output_path,
                                                                 flux_cal_field, phase_cal_fields,
                                                                 spw, refant, minsnr)
        self._run(script_path, script_parameters)

    def apply_target_source_calibration(self, source_config, source_id):
        logger.info(Color.HEADER + "Applying Calibration to Target Source..." + Color.ENDC)
        flux_cal_fields = ",".join(map(str, config.GLOBAL_CONFIG['flux_cal_fields']))
        phase_cal_fields = ",".join(map(str, config.GLOBAL_CONFIG['target_phase_src_map'][source_id]))
        script_path = 'casa_scripts/target_source_calibration.py'
        script_parameters = "{0} {1} {2} {3} {4}".format(self._dataset_path, self._output_path,
                                                         flux_cal_fields, phase_cal_fields,
                                                         source_id)
        self._run(script_path, script_parameters)

    def r_flag(self, source_type):
        script_path = 'casa_scripts/r_flag.py'
        script_parameters = "{0} {1} {2}".format(self._dataset_path, source_type, config.CONFIG_PATH)
        logger.info(Color.HEADER + "Running Rflag auto-flagging algorithm" + Color.ENDC)
        self._run(script_path, script_parameters)

    def tfcrop(self, source_type):
        script_path = 'casa_scripts/tfcrop.py'
        script_parameters = "{0} {1} {2}".format(self._dataset_path, source_type, config.CONFIG_PATH)
        logger.info(Color.HEADER + "Running Tfcrop auto-flagging algorithm" + Color.ENDC)
        self._run(script_path, script_parameters)

    def setjy(self, source_id, source_name):
        logger.info(Color.HEADER + 'Running setjy' + Color.ENDC)
        script_path = 'casa_scripts/setjy.py'
        freq_band = "L"
        model_path = "{0}/{1}_{2}.im".format(config.CASA_CONFIG['casa'][platform.system()]['model_path'],
                                             source_name.split("_")[0], freq_band)
        script_parameters = "{0} {1} {2} {3}".format(config.GLOBAL_CONFIG['spw_range'], self._dataset_path, source_id,
                                                     model_path)
        self._run(script_path, script_parameters)

    def split(self, output_path, filters):
        script_path = 'casa_scripts/split_dataset.py'
        logger.info(Color.HEADER + "Splitting dataset at location {0}".format(output_path) + Color.ENDC)
        spw = filters.get("spw", "all")
        width = filters.get("width", '1')
        field = filters.get("field", 0)

        if spw != "all":
            spw = format_spw_with_channels(spw, filters.get("channels_to_avg", ''))

        script_parameters = "{0} {1} {2} {3} {4} {5}".format(self._dataset_path, output_path, field,
                                                             filters['datacolumn'], width, spw)
        self._run(script_path, script_parameters)

    def base_image(self):
        logger.info(Color.HEADER + "Creating base image for {0}".format(self._dataset_path) + Color.ENDC)
        script_path = 'casa_scripts/base_image.py'
        script_parameters = "{0} {1} {2}".format(self._dataset_path, self._output_path, config.CONFIG_PATH)

        self._run(script_path, script_parameters)

    def apply_self_calibration(self, self_cal_config, calibration_mode, output_ms_path, output_path, spw):
        logger.info(Color.HEADER + "Applying self calibration for {0}".format(self._dataset_path) + Color.ENDC)
        cal_mode = self_cal_config['calmode']
        mask_path = self_cal_config['masking']['mask_path'] if self_cal_config['masking']['mask_path'] else 'None'

        script_path = 'casa_scripts/self_calibration.py'
        script_parameters = "{0} {1} {2} {3} {4} {5} {6} {7} {8} {9} {10} {11} {12} {13} " \
                            "{14} {15} {16} {17} {18}".format(config.CONFIG_PATH,
                                                         self._dataset_path,
                                                         output_path,
                                                         output_ms_path,
                                                         cal_mode[calibration_mode]['solint'],
                                                         config.GLOBAL_CONFIG['refant'],
                                                         self_cal_config['minsnr'],
                                                         self._output_path,
                                                         cal_mode[calibration_mode]['applymode'],
                                                         self_cal_config['masking']['threshold'],
                                                         self_cal_config['masking']['bmask']['bottom_left_corner'][
                                                             'x_coordinate'],
                                                         self_cal_config['masking']['bmask']['bottom_left_corner'][
                                                             'y_coordinate'],
                                                         self_cal_config['masking']['bmask']['top_right_corner'][
                                                             'x_coordinate'],
                                                         self_cal_config['masking']['bmask']['top_right_corner'][
                                                             'y_coordinate'],
                                                         mask_path,
                                                         cal_mode['ap']['loop_count'],
                                                         cal_mode['p']['loop_count'],
                                                         calibration_mode,
                                                         spw)

        self._run(script_path, script_parameters)

    def fourier_transform(self, field_name, cal_mode, spw_range, loop_count):
        logger.info(Color.HEADER + "Calculating fourier transform on {0}".format(field_name) + Color.ENDC)
        script_path = 'casa_scripts/fourier_transform.py'
        script_parameters = "{0} {1} {2} {3} {4} {5}".format(spw_range, self._output_path, cal_mode, loop_count,
                                                             self._dataset_path,
                                                             field_name)

        self._run(script_path, script_parameters)

    def apply_line_calibration(self, calmode_config, source_id, mode):
        logger.info(Color.HEADER + "Applying calibration on Line.." + Color.ENDC)
        script_path = 'casa_scripts/apply_line_calibration.py'
        p_loop_count = calmode_config["p"]["loop_count"]
        ap_loop_count = calmode_config["ap"]["loop_count"]
        p_table = '{0}/self_caled_p_{1}_{2}/p_selfcaltable_{3}.gcal'.format(config.OUTPUT_PATH, mode, source_id,
                                                                            p_loop_count)
        ap_table = '{0}/self_caled_ap_{1}_{2}/ap_selfcaltable_{3}.gcal'.format(config.OUTPUT_PATH, mode, source_id,
                                                                               ap_loop_count)
        script_parameters = "{0} {1} {2} {3} {4}".format(p_loop_count, ap_loop_count, ap_table, p_table,
                                                         self._dataset_path)
        self._run(script_path, script_parameters)

    def extend_continuum_flags(self, source_id):
        logger.info(Color.HEADER + "Extending continuum flags on line..." + Color.ENDC)
        flag_reasons = "{0},{1}".format(BAD_ANTENNA_TIME, BAD_BASELINE_TIME)
        self.flagdata(flag_reasons, config.OUTPUT_PATH + "/continuum_ref_{0}/".format(source_id))

    def create_line_image(self):
        logger.info(Color.HEADER + "Creating line image at {0}".format(self._output_path) + Color.ENDC)
        script_path = 'casa_scripts/create_line_image.py'
        script_parameters = "{0} {1} {2} {3}".format(
            config.GLOBAL_CONFIG['spw_range'],
            self._dataset_path,
            self._output_path,
            config.CONFIG_PATH)
        self._run(script_path, script_parameters)

    def _unlock_dataset(self):
        table = casac.casac.table()
        table.open(self._dataset_path)
        table.unlock()

    def _form_casa_command(self, script, script_parameters):
        casa_path = config.CASA_CONFIG['casa'][platform.system()]['path']
        logfile = config.OUTPUT_PATH + "/casa.log"
        script_full_path = os.path.realpath(script)
        casa_command = "{0} --nologger --nogui  --logfile {1} -c {2} {3}" \
            .format(casa_path, logfile, script_full_path, script_parameters)
        return casa_command

    def _form_mpi_command(self, script, script_parameters):
        mpi_config = config.CASA_CONFIG['mpicasa']
        mpi_command = "mpicasa -n {0}".format(mpi_config['n'])
        if mpi_config['hostfile']:
            mpi_command += " --hostfile {0} ".format(mpi_config['hostfile'])

        mpi_command += " --mca btl_tcp_if_include {0} --mca oob_tcp_if_include {1}  " \
            .format(mpi_config['mca']['btl_tcp_if_include'],
                    mpi_config['mca']['oob_tcp_if_include'])

        casa_command = self._form_casa_command(script, script_parameters)
        return mpi_command + casa_command

    def _run(self, script, script_parameters=None):
        casa_output_file = config.OUTPUT_PATH + "/casa_output.txt"
        if not script_parameters: script_parameters = self._dataset_path
        self._unlock_dataset()

        if config.CASA_CONFIG['is_parallel']:
            command = self._form_mpi_command(script, script_parameters)
        else:
            command = self._form_casa_command(script, script_parameters)

        logger.debug("Executing command -> " + command)
        subprocess.Popen(command, stdin=subprocess.PIPE, stdout=file(casa_output_file, 'a+'), shell=True).wait()
