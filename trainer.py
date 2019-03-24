# -*- coding: utf-8 -*-

import json
import struct

from dic import Dic

class Trainer:
    def __init__(self, dic):
        self.dic = dic
        self.dic_size = self.dic.size()
        self.count = [0] * self.dic_size
        self.mat = [[0.0 for j in range(self.dic_size)] for i in range(self.dic_size)]
        return

    def write_into_file(self, output_path):
        print('Writing into file ' + output_path + ' ... ', end='', flush=True)
        with open(output_path, 'wb') as f:
            f.write(struct.pack('i', self.dic_size))
            for i in self.count:
                f.write(struct.pack('i', i))
            for i in range(self.dic_size):
                for j in range(self.dic_size):
                    f.write(struct.pack('f', self.mat[i][j]))
        print('done !')
        return

    def analyze_sentence(self, sentence):
        for ch in sentence:
            self.count[self.dic.chs[ch]] += 1
        for i in range(0, len(sentence) - 1):
            self.insert_word(sentence[i], sentence[i + 1])
        return

    def insert_word(self, cha, chb):
        self.mat[self.dic.chs[cha]][self.dic.chs[chb]] += 1.0
        return

    def build(self):
        print('Building final mat file ... ', end='', flush=True)
        for i in range(self.dic_size):
            if self.count[i] == 0:
                continue
            for j in range(self.dic_size):
                self.mat[i][j] /= self.count[i]
        print('done !')
        return

    def analyze(self, data):
        sentence = ''
        for ch in data:
            if self.dic.has_key(ch):
                sentence += ch
            else:
                self.analyze_sentence(sentence)
                sentence = ''
        return

    def feed(self, data_path):
        print('Feeding data in ' + data_path + ' ... ', end='', flush=True)
        with open(data_path, 'r') as f:
            for line in f.readlines():
                data = json.loads(line)['html']
                self.analyze(data)
        print('done !')
        return

def train(config_path):
    print('Loading training config ... ', end='', flush=True)
    with open(config_path, 'r') as f:
        config = json.load(f)
    n_gram = config['n_gram']
    assert n_gram == 2 or n_gram == 3
    print('done !')

    dic = Dic()
    dic.read_dict(config['dic'])
    
    trainer = Trainer(dic)
    for data in config['data']:
        trainer.feed(data)
    trainer.build()
    trainer.write_into_file(config['model'])