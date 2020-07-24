#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import dwgconfig


def create_logger(debug=False):
    log = logging.getLogger()
    formatter = logging.Formatter(dwgconfig.log_format, datefmt=dwgconfig.log_date_format)
    log_level = logging.DEBUG
    if debug:
        log_handler = logging.StreamHandler()
    else:
        if not dwgconfig.debug:
            log_level = logging.INFO
        log_handler = logging.FileHandler(dwgconfig.logfile)
    log_handler.setLevel(log_level)
    log_handler.setFormatter(formatter)
    log.setLevel(log_level)
    log.addHandler(log_handler)
