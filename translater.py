# -*- coding: utf-8 -*-

import json
import struct

from dic import Dic

class Translater:
    def __init__(self, dic, n_gram, model_path):
        self.dic = dic
        self.n_gram = n_gram
        self.load_model(model_path)
        self.set_weight(0.3, 0.00001)
        self.wng = {}
        self.set_weight_ng(0.9, 0.1, 0.01, 0.01, 0.98, 1)
        return

    def set_weight_ng(self, a, b, c, d, e, q):
        self.wng['a'] = a
        self.wng['b'] = b
        self.wng['c'] = c
        self.wng['d'] = d
        self.wng['e'] = e
        self.wng['q'] = q
        return

    def set_weight(self, a, g):
        self.alpha = a
        self.gamma = g
        self.beta = 1 - a - g

    def load_model(self, model_path):
        print('Loading model ' + model_path + ' ... ', end='', flush=True)
        with open(model_path, 'rb') as f:
            (self.dic_size,) = struct.unpack('i', f.read(4))
            count = struct.unpack(str(self.dic_size) + 'i', f.read(4 * self.dic_size))
            total = 0
            for i in count:
                total += i
            self.c_poss = [i / (1.0 * total) for i in count]
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
            if py == 'exit' or py == '':
                break
            else:
                args = py.split()
                if len(args[0]) == 1 and args[0] >= 'a' and args[0] <= 'z':
                    self.wng[args[0]] = float(args[1])
                else:
                    print('Result: ' + self.translate_sentence_ng3(py))
        return

    def calc_poss(self, curr, next):
        if curr == -1: cc = ''
        else: cc = self.dic.set[curr]
        nc = self.dic.set[next]
        # if self.c_poss[next] > 1e-3:
        #   print(self.dic.set[next])
        #   print(self.c_poss[next])
        poss = self.gamma * max(2 * self.dic.word_predict(cc + nc), 0.01 * self.dic.word_predict(nc))
        poss += self.c_poss[next] * self.alpha
        if curr == -1:
            return poss
        # if self.mat[curr][next]:
        #    print(self.dic.set[curr] + self.dic.set[next])
        #    print(self.mat[curr][next])
        #    print(max(2 * self.dic.word_predict(cc + nc), 0.01 * self.dic.word_predict(nc)))
        poss += self.mat[curr][next] * self.beta
        return poss

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
                bid = self.dic.chs[ch + proc]
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

    def calc_poss_ng(self, lc, nc, npos, lp):
        poss = 0
        # print(self.dic.set[lc] + self.dic.set[nc], npos)
        if npos == 0: # new word
            poss += self.wng['c'] * self.dic.predict_acc_bk(lc, lp)
            poss += self.wng['d'] * self.dic.predict_acc_ft(nc)
            if lc != -1:
                poss += self.wng['e'] * self.mat[lc][nc]
                poss *= self.wng['q']
        else:
            poss += self.wng['a'] * self.dic.predict_acc_ct(lc, nc, npos - 1) # continue npos
            if lc != -1:
                poss += self.wng['b'] * self.mat[lc][nc] # a new word
        # print(poss, flush=True)
        return poss

    def calc_poss_ng3(self, l2c, nc, npos, lp, aa='', bb=''):
        poss = 0
        llc = l2c >> 16; lc = l2c & 65535
        if llc == 19981: llc = -1
        if lc == 19981: lc = -1
        if llc == -1:
            return self.calc_poss_ng(lc, nc, npos, lp)
        if npos == 0: # break
            poss += self.wng['c'] * self.dic.predict_acc_bk(lc, lp)
            poss += self.wng['d'] * self.dic.predict_acc_ft(nc)
            if lc != -1:
                poss += self.wng['e'] * self.mat[lc][nc]
                poss *= self.wng['q']
        else:
            poss += self.wng['a'] * self.dic.acc_word_ct3(l2c, nc)
            poss += self.wng['b'] * self.mat[lc][nc] # new word
        if self.dic.set[llc] == '神' and self.dic.set[lc] == '经' and self.dic.set[nc] == '网':
            print((self.dic.set[nc], poss, aa, bb))
        if self.dic.set[llc] == '经' and self.dic.set[lc] == '网' and self.dic.set[nc] == '络':
            print((self.dic.set[nc], poss, aa, bb))      
        if self.dic.set[nc] == '望' and npos == 0:
            print((self.dic.set[nc], poss, aa, bb))
        return poss

    def translate_sentence_ng3(self, sentence):
        procs = sentence.split()
        if len(procs) <= 2:
            return self.translate_sentence_ng(sentence)
        for i in range(len(procs)):
            procs[i] = procs[i].lower()
        l1_chs = [19981]
        l2_chs = [(19981 << 16) | 19981] # lucky number
        f = [[1.0] * 7]; g = [[''] * 7]
        loop_i = 0
        for proc in procs:
            loop_i += 1
            n_f = []; n_g = []
            c1_chs = [self.dic.chs[ch + proc] for ch in self.dic.map[proc]]
            c2_chs = []
            for lc in l1_chs:
                for ch in self.dic.map[proc]:
                    bid = self.dic.chs[ch + proc]
                    c2_chs.append((lc << 16) | bid)
                    sv_f = []; sv_g = []
                    # a new beginning
                    max_poss = -1; max_cp = ''
                    for i in range(7):
                        for lc2_id in range(len(l2_chs)):
                            if not ((l2_chs[lc2_id] & 65535) == lc): continue
                            poss = self.calc_poss_ng3(l2_chs[lc2_id], bid, 0, i) * f[lc2_id][i]
                            tmp_cp = g[lc2_id][i]
                            t = tmp_cp.split('/')
                            poss *= self.dic.freq(t[len(t) - 1])
                            if poss > max_poss:
                                max_poss = poss
                                max_cp = tmp_cp + '/' + ch
                    sv_f.append(max_poss); sv_g.append(max_cp)
                    # continue a word
                    for i in range(1, 7):
                        max_poss = -1; max_cp = ''
                        for lc2_id in range(len(l2_chs)):
                            if not ((l2_chs[lc2_id] & 65535) == lc): continue
                            poss = self.calc_poss_ng3(l2_chs[lc2_id], bid, i, i, g[lc2_id][i - 1], f[lc2_id][i - 1]) * f[lc2_id][i - 1]
                            tmp_cp = g[lc2_id][i - 1] + ch
                            if loop_i == len(procs):
                                t = tmp_cp.split('/')
                                poss *= self.dic.freq(t[len(t) - 1])
                            if poss > max_poss:
                                max_poss = poss
                                max_cp = tmp_cp
                            sv_f.append(max_poss); sv_g.append(max_cp)
                    n_f.append(sv_f); n_g.append(sv_g)
            f = n_f; g = n_g
            l1_chs = c1_chs; l2_chs = c2_chs
        max_poss = -1; answer = ''
        for i in range(len(f)):
            for j in range(7):
                if f[i][j] > max_poss:
                    max_poss = f[i][j]
                    answer = g[i][j]
        return answer

    def translate_sentence_ng(self, sentence):
        procs = sentence.split()
        if not len(procs):
            return ''
        for i in range(len(procs)):
            procs[i] = procs[i].lower()
        last_chs = [-1]; f = [[1.0] * 7]; g = [[''] * 7]
        loop_i = 0
        for proc in procs:
            loop_i += 1
            n_f = []; n_g = []; curr_chs = []
            for ch in self.dic.map[proc]:
                bid = self.dic.chs[ch + proc]
                curr_chs.append(bid)
                sv_f = []; sv_g = []
                # a new beginning
                max_poss = -1; max_cp = ''
                for i in range(7):
                    for lc_id in range(len(last_chs)):
                        poss = self.calc_poss_ng(last_chs[lc_id], bid, 0, i) * f[lc_id][i]
                        tmp_cp = g[lc_id][i]
                        t = tmp_cp.split('/')
                        poss *= self.dic.freq(t[len(t) - 1])
                        if poss > max_poss:
                            max_poss = poss
                            max_cp = tmp_cp + '/' + ch
                sv_f.append(max_poss); sv_g.append(max_cp)
                # continue a word
                for i in range(1, 7):
                    max_poss = -1; max_cp = ''
                    for lc_id in range(len(last_chs)):
                        poss = self.calc_poss_ng(last_chs[lc_id], bid, i, i) * f[lc_id][i - 1]
                        tmp_cp = g[lc_id][i - 1] + ch
                        if loop_i == len(procs):
                            t = tmp_cp.split('/')
                            poss *= self.dic.freq(t[len(t) - 1])
                        if poss > max_poss:
                            max_poss = poss
                            max_cp = tmp_cp
                    sv_f.append(max_poss); sv_g.append(max_cp)
                n_f.append(sv_f); n_g.append(sv_g)
            last_chs = curr_chs
            f = n_f; g = n_g
        max_poss = -1; answer = ''
        for i in range(len(f)):
            for j in range(7):
                if f[i][j] > max_poss:
                    max_poss = f[i][j]
                    answer = g[i][j]
        return answer

    def translate_file(self, input_path, output_path):
        print('Translating file ' + input_path + ' to ' + output_path + ' ... ', end='', flush=True)
        with open(input_path, 'r') as input:
            with open(output_path, 'w') as output:
                for line in input.readlines():
                    output.write(self.translate_sentence_ng3(line))
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
    dic.read_dict(config['dic'], config['word'], True)
    
    translater = Translater(dic, n_gram, config['model'])
    if input_path == '':
        translater.shell()
    else:
        translater.translate_file(input_path, output_path) 
    return