#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import constants
from DataCollector import DataCollector

# REDDIT
reddit_collector = DataCollector(constants.REDDIT_NAME)
reddit_collector.collect_data_today()
reddit_collector.save_data()

