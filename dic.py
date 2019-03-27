# -*- coding: utf-8 -*-

from pypinyin import lazy_pinyin

class Dic:
    def __init__(self):
        self.ch_count = 0
        self.map = {} # pinyin to char
        self.map[''] = -1
        self.chs = {} # char+pingyin to id
        self.set = [] # id to char
        self.set_py = [] # cid to pinyin
        self.map_py = {} # pinyin to pid
        self.rhs = {} # chars to procs
        self.wdb = {} # wordbook
        self.pyc = {} # py count
        self.awc = [] # all count
        self.lacc = {} # word to acc dict
        self.pacc = {} # pinyin to count
        self.cacc = [] # char to acc array
        self.cacc_bk = [] # char to bk array
        self.cacc_py = [] # id, py, dict
        self.thg = {} # 3 count
        self.thg_t = {} # 2 in 3 count
        self.word_count = 0
        return

    def size(self):
        return self.ch_count

    def has_key(self, ch):
        return ch in self.rhs

    def convert_pinyin(self, ch, pinyin):
        if not pinyin in self.rhs[ch]:
            return self.rhs[ch][0]
        if pinyin == 'lve': return 'lue'
        if pinyin == 'nve': return 'nue'
        return pinyin

    def push(self, ch, py):
        self.set.append(ch)
        self.set_py.append(py)
        self.pyc[py] = 0
        self.pacc[py] = [0] * 7
        self.cacc.append([0] * 7)
        self.awc.append(0)
        self.cacc_bk.append([0] * 7)
        self.cacc_py.append([{}, {}, {}, {}, {}, {}, {}])
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

    def iword(self, word, pos, count):
        if pos >= 7:
            return
        if not word in self.lacc:
            self.lacc[word] = [0] * 7
        self.lacc[word][pos] += count
        return

    def freq(self, word, l):
        if word == '':
            return 1
        if not word in self.wdb:
            return 0.01
            
        # if len(word) >= 5:
        #     print('q' + word)
        #     print(min(1.0 * self.wdb[word] / self.word_count * (l ** len(word)), 2.0))
        # if len(word) >= 4 and word[1:4] == '经网络':
        #     print((word, max(0.2, min(1.0 * self.wdb[word] / self.word_count * 100000, 1.0))))
        return min(1.0 * self.wdb[word] / self.word_count * (l ** (len(word) * 2)), 2.0)

    def iword2(self, lc, npos, py, count):
        if npos >= 7:
            return
        if not py in self.cacc_py[lc][npos]:
            self.cacc_py[lc][npos][py] = 0
        self.cacc_py[lc][npos][py] += count
        return

    def ichar(self, ch, pos, count, last=False):
        if pos >= 7:
            return
        self.cacc[ch][pos] += count
        self.awc[ch] += count
        self.pyc[self.set_py[ch]] += count
        self.pacc[self.set_py[ch]][pos] += count
        if last:
            self.cacc_bk[ch][pos] += count
        return

    def ituple(self, key, count):
        if not key in self.thg:
            self.thg[key] = 0
        self.thg[key] += count
        return

    def ituple2(self, key, count):
        if not key in self.thg_t:
            self.thg_t[key] = 0
        self.thg_t[key] += count
        return

    def combine_ch(self, c, p):
        return self.chs[c + p]

    def combine_word(self, c1, p1, c2, p2):
        return (self.chs[c1 + p1] << 16) | (self.chs[c2 + p2])

    def combine_word3(self, c1, p1, c2, p2, c3, p3):
        return (self.chs[c1 + p1] << 32) | (self.chs[c2 + p2] << 16) | (self.chs[c3 + p3])

    def load_acc_word(self, word, count, py):
        for i in range(len(word) - 1):
            self.iword(self.combine_word(word[i], py[i], word[i + 1], py[i + 1]), i, count)
            self.iword2(self.combine_ch(word[i], py[i]), i, py[i + 1], count)
            self.ichar(self.combine_ch(word[i], py[i]), i, count)
        for i in range(len(word) - 2):
            self.ituple(self.combine_word3(word[i], py[i], word[i + 1], py[i + 1], word[i + 2], py[i + 2]), count)
            self.ituple2((self.combine_word(word[i], py[i], word[i + 1], py[i + 1]) << 16) | self.map_py[py[i + 2]], count)
        self.ichar(self.combine_ch(word[len(word) - 1], py[len(py) - 1]), len(word) - 1, count, last=True)
        return

    def acc_sum_pos(self, ch):
        sum = 0
        for i in self.cacc[ch]:
            sum += i
        return sum

    def acc_sum_pos_py(self, py):
        sum = 0
        for i in self.pacc[py]:
            sum += i
        return sum

    def acc_word_ct(self, lc, nc, npos):
        word = (lc << 16) + nc
        if not word in self.lacc:
            return 0
        return self.lacc[word][npos]

    def acc_word_ct3(self, llc, nc):
        word = (llc << 16) | nc
        llc = (llc << 16) | self.map_py[self.set_py[nc]]
        if (not llc in self.thg_t) or (not word in self.thg):
            return 0
        return float(self.thg[word]) / float(self.thg_t[llc])

    def acc_ks(self, lc, npos, py):
        if not py in self.cacc_py[lc][npos]:
            return 0
        return self.cacc_py[lc][npos][py]

    def predict_acc_bk(self, ch, pos):
        if ch == -1:
            return 0
        if self.cacc[ch][pos] == 0:
            return 0
        return float(self.cacc_bk[ch][pos]) / float(self.cacc[ch][pos])

    def predict_acc_ft(self, ch):
        sum = self.acc_sum_pos_py(self.set_py[ch])
        if sum == 0:
            return 0
        return min(30 * float(self.cacc[ch][0]) / float(sum), 1.0)

    def predict_acc_ct(self, lc, nc, npos):
        if lc == -1:
            return 0
        count = self.acc_word_ct(lc, nc, npos)
        sum = self.acc_ks(lc, npos, self.set_py[nc])
        if sum == 0:
            return 0
        return float(count) / float(sum)

    def read_dict(self, dict_path, word_path, lacc=False):
        print('Reading dictionary file ... ', end='', flush=True)
        with open(dict_path, 'r') as f:
            py_count = 0
            for line in f.readlines():
                data = line.split()
                self.map[data[0]] = data[1:]
                self.map_py[data[0]] = py_count
                py_count += 1
                for ch in data[1:]:
                    self.push(ch, data[0])
        with open(word_path, 'r') as f:
            for line in f.readlines():
                [w, c, v] = line.split()
                hans = True
                for ch in w:
                    if not ch in self.rhs:
                        hans = False
                        break
                if not hans:
                    continue
                self.wdb[w] = int(c)
                self.word_count += int(c)
                if lacc:
                    py = lazy_pinyin(w, strict=False)
                    py = [self.convert_pinyin(w[i], py[i]) for i in range(len(py))]
                    self.load_acc_word(w, int(c), py)
        print('done !')
        return