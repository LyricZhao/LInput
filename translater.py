# -*- coding: utf-8 -*-

import json
import struct

from dic import Dic

class Translater:
    def __init__(self, dic, n_gram, model_path):
        self.dic = dic
        self.n_gram = n_gram
        self.load_model(model_path)
        self.alpha = 0.2
        self.beta = 1 - self.alpha
        return

    def load_model(self, model_path):
        print('Loading model ' + model_path + ' ... ', end='', flush=True)
        with open(model_path, 'rb') as f:
            (self.dic_size,) = struct.unpack('i', f.read(4))
            count = struct.unpack(str(self.dic_size) + 'i', f.read(4 * self.dic_size))
            self.c_poss = [i / (1.0 * self.dic_size) for i in count]
            del count
            mat_data = struct.unpack(str(self.dic_size * self.dic_size) + 'f', f.read(4 * self.dic_size * self.dic_size))
            self.mat = [[ mat_data[i * self.dic_size + j] for j in range(self.dic_size)] for i in range(self.dic_size)]
            del mat_data
        print('done !')
        return

    def shell(self):
        print('Pinyin Shell: type pinyin and translate, exit to quit')
        while True:
            py = input('Pinyin: ')
            if py == 'exit':
                break
            else:
                print('Result: ' + self.translate_sentence(py))
        return

    def calc_poss(self, curr, next):
        if curr == -1:
            return self.c_poss[next]
        return self.c_poss[next] * self.alpha + self.mat[curr][next] * self.beta

    def translate_sentence(self, sentence):
        procs = sentence.split()
        if not len(procs):
            return ''
        for i in range(len(procs)):
            procs[i] = procs[i].lower()
        # f[k]: possiblity, g[]: result
        last_chs = [-1]; f = [1.0]; g = ['']
        for proc in procs:
            n_f = []; n_g = []; curr_chs = []
            for ch in self.dic.map[proc]:
                bid = self.dic.chs[ch]
                curr_chs.append(bid)
                max_poss = -1; max_cp = ''
                for lc_id in range(len(last_chs)):
                    poss = self.calc_poss(last_chs[lc_id], bid) * f[lc_id]
                    if poss > max_poss:
                        max_poss = poss
                        max_cp = g[lc_id] + ch
                n_f.append(max_poss)
                n_g.append(max_cp)
            last_chs = curr_chs
            f = n_f; g = n_g
        max_poss = -1; answer = ''
        for i in range(len(f)):
            if f[i] > max_poss:
                max_poss = f[i]
                answer = g[i]
        return answer

    def translate_file(self, input_path, output_path):
        print('Translating file ' + input_path + ' to ' + output_path + ' ... ', end='', flush=True)
        with open(input_path, 'r') as input:
            with open(output_path, 'w') as output:
                for line in input.readlines():
                    output.write(self.translate_sentence(line))
        print('done !')
        return 

def translate(config_path, input_path, output_path):
    print('Loading config ... ', end='', flush=True)
    with open(config_path, 'r') as f:
        config = json.load(f)
    n_gram = config['n_gram']
    assert n_gram == 2 or n_gram == 3
    print('done !')

    dic = Dic()
    dic.read_dict(config['dic'])
    
    translater = Translater(dic, n_gram, config['model'])
    if input_path == '':
        translater.shell()
    else:
        translater.translate_file(input_path, output_path) 
    return