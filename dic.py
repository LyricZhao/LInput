# -*- coding: utf-8 -*-

class Dic:
    def __init__(self):
        self.ch_count = 0
        self.map = {} # pinyin to char
        self.map[''] = -1
        self.chs = {} # char to id
        self.set = [] # id to char
        return

    def size(self):
        return self.ch_count

    def has_key(self, ch):
        return ch in self.chs

    def push(self, ch):
        if not ch in self.chs:
            self.set.append(ch)
            self.chs[ch] = self.ch_count
            self.ch_count += 1
        return 

    def read_dict(self, dict_path):
        print('Reading dictionary file ... ', end='', flush=True)
        with open(dict_path, 'r') as f:
            for line in f.readlines():
                data = line.split()
                self.map[data[0]] = data[1:]
                for ch in data[1:]:
                    self.push(ch)
        print('done !')
        return