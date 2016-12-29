import os
from sys import path

from pybuilder.core import use_plugin, init, task

path.append("src/main/python")

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin("python.coverage")

name = "artip"
default_task = ["clean", "install_dependencies", "publish"]


@init
def set_dependencies(project):
    # Build dependencies
    project.build_depends_on('mock')
    project.build_depends_on('coloredlogs')


@init
def set_properties(project):
    project.set_property('coverage_threshold_warn', 60)
    project.set_property('coverage_break_build', False)
    project.set_property("coverage_exceptions", ['models', 'plotter'])


@task
def run_unit_tests(logger):
    logger.info("Coverage File Path : %s/target/reports/coverage_html/index.html", os.getcwd())
