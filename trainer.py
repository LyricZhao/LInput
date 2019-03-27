# -*- coding: utf-8 -*-

import json
import struct
import jieba

from pypinyin import lazy_pinyin
from dic import Dic

class Trainer:
    def __init__(self, dic):
        self.dic = dic
        self.step = 0.05
        self.jieba = True
        self.dic_size = self.dic.size()
        self.count = [0] * self.dic_size
        self.mat = [[0.0 for j in range(self.dic_size)] for i in range(self.dic_size)]
        self.sepy = {}
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
        word_cut = jieba.cut(sentence)
        word_cut = [w for w in word_cut]
        cur_pos = -1
        for i in range(len(word_cut) - 1):
            cur_pos += len(word_cut[i])
            assert cur_pos >= 0
            self.count[self.dic.chs[sentence[cur_pos] + pinyin[cur_pos]]] += count
            self.insert_word(sentence[cur_pos] + pinyin[cur_pos], sentence[cur_pos + 1] + pinyin[cur_pos + 1], count)
        return

    def insert_word(self, cha, chb, count):
        self.mat[self.dic.chs[cha]][self.dic.chs[chb]] += count
        py_key = (self.dic.chs[cha] << 16) | self.dic.map_py[(self.dic.set_py[self.dic.chs[chb]])]
        if not py_key in self.sepy:
            self.sepy[py_key] = 0
        self.sepy[py_key] += count
        return

    def query_cp_sum(self, i, j):
        py_key = (i << 16) | self.dic.map_py[(self.dic.set_py[j])]
        if not py_key in self.sepy:
            return 0
        return self.sepy[py_key]

    def build(self):
        print('Building final mat file ... ', end='', flush=True)
        for i in range(self.dic_size):
            for j in range(self.dic_size):
                sum = self.query_cp_sum(i, j)
                if sum == 0:
                    continue
                self.mat[i][j] /= sum
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

    def feed(self, data_path, jbc=False):
        print('Feeding data in ' + data_path + ' ... ', flush=True)
        with open(data_path, 'r') as f:
            lines = f.readlines()
            prog = 0; tot = len(lines); target = self.step
            for line in lines:
                data = json.loads(line)['html']
                self.analyze(data)
                prog += 1
                if (float(prog) / tot) >= target - 1e-5:
                    print('- Current progress: ' + str(target * 100) + ' %', flush=True)
                    target += self.step
        print('- done !')
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
    # trainer.feed(config['word'], True)
    for data in config['data']:
        trainer.feed(data)
    trainer.build()
    trainer.write_into_file(config['model'])