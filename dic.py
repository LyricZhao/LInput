# -*- coding: utf-8 -*-

class Dic:
    def __init__(self):
        self.ch_count = 0
        self.map = {} # pinyin to char
        self.map[''] = -1
        self.chs = {} # char+pingyin to id
        self.set = [] # id to char
        self.rhs = {} # chars to procs
        self.wdb = {} # wordbook
        self.word_count = 0
        return

    def size(self):
        return self.ch_count

    def has_key(self, ch):
        return ch in self.rhs

    def push(self, ch, py):
        self.set.append(ch)
        self.chs[ch + py] = self.ch_count
        self.ch_count += 1
        if not ch in self.rhs:
            self.rhs[ch] = []
        self.rhs[ch].append(py)
        return 

    def word_predict(self, word):
        if word in self.wdb:
            return min(9000 * self.wdb[word] / (1.0 * self.word_count), 0.2)
        return 0

    def read_dict(self, dict_path, word_path):
        print('Reading dictionary file ... ', end='', flush=True)
        with open(dict_path, 'r') as f:
            for line in f.readlines():
                data = line.split()
                self.map[data[0]] = data[1:]
                for ch in data[1:]:
                    self.push(ch, data[0])
        with open(word_path, 'r') as f:
            for line in f.readlines():
                [w, c, v] = line.split()
                self.wdb[w] = int(c)
                self.word_count += int(c)
        print('done !')
        return