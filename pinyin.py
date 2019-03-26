# -*- coding: utf-8 -*-

import argparse

import trainer
import translater

parser = argparse.ArgumentParser(description='LInput: Pinyin to Chinese; Author: Chenggang Zhao, CST 75')
parser.add_argument('--train', type=str, default='', help='Training dataset config path')
parser.add_argument('--test', type=str, default='', help='Test condig path')
parser.add_argument('--input', type=str, default='', help='Input file path for test mode')
parser.add_argument('--output', type=str, default='', help='Output file path for test mode')

options = parser.parse_args()
if options.train != '':
    trainer.train(options.train)

if options.test != '':
    translater.translate(options.test, options.input, options.output)