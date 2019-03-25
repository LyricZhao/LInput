# -*- coding: utf-8 -*-

import json
import struct
import jieba

from pypinyin import lazy_pinyin
from dic import Dic

class Trainer:
    def __init__(self, dic):
        self.dic = dic
        self.jieba = True
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

    def convert_pinyin(self, ch, pinyin):
        if not pinyin in self.dic.rhs[ch]:
            return self.dic.rhs[ch][0]
        if pinyin == 'lve': return 'lue'
        if pinyin == 'nve': return 'nue'
        return pinyin

    def analyze_sentence(self, sentence, count=1):
        # print(sentence)
        pinyin = lazy_pinyin(sentence, strict=False)
        pinyin = [self.convert_pinyin(sentence[i], pinyin[i]) for i in range(len(pinyin))]
        for i in range(len(sentence)):
            self.count[self.dic.chs[sentence[i] + pinyin[i]]] += count
        for i in range(len(sentence) - 1):
            self.insert_word(sentence[i] + pinyin[i], sentence[i + 1] + pinyin[i + 1], count)
        return

    def insert_word(self, cha, chb, count):
        self.mat[self.dic.chs[cha]][self.dic.chs[chb]] += count
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
                if self.jieba:
                    for words in jieba.cut(sentence, cut_all=True):
                        self.analyze_sentence(words)
                sentence = ''
        return

    def feed(self, data_path, jbc=False):
        print('Feeding data in ' + data_path + ' ... ', end='', flush=True)
        if jbc:
            with open(data_path, 'r') as f:
                for line in f.readlines():
                    [w, c, v] = line.split()
                    in_dict = True
                    for ch in w:
                        in_dict &= self.dic.has_key(ch)
                    if in_dict:
                        self.analyze_sentence(w, int(c))
        else:  
            with open(data_path, 'r') as f:
                for line in f.readlines():
                    data = json.loads(line)['html']
                    self.analyze(data)
        print('done !')
        return

def train(config_path):
    jieba.initialize() # init jieba
    print('Loading training config ... ', end='', flush=True)
    with open(config_path, 'r') as f:
        config = json.load(f)
    n_gram = config['n_gram']
    assert n_gram == 2 or n_gram == 3
    print('done !')

    dic = Dic()
    dic.read_dict(config['dic'], config['word'])
    
    trainer = Trainer(dic)
    trainer.feed(config['word'], True)
    for data in config['data']:
        trainer.feed(data)
    trainer.build()
    trainer.write_into_file(config['model'])