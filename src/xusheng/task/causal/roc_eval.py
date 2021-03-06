# Author: Xusheng Luo
# Evaluate acc. of cause/effect identification on copa dataset

import numpy as np
from scipy import dot, linalg
from xusheng.util.log_util import LogInfo

class ROC_evaluator(object):

    def __init__(self):
        self.sync = dict()
        self.syne_neg = dict()
        self.sync_neg = dict()
        self.syne = dict()
        self.copa_data = list()
        self.copa_ground = list()
        self.load_data()

    def load_data(self):
        """
        load data from files
        :return: 
        """
        LogInfo.begin_track("Loading data...")
        with open("/home/yuchen/CppFiles/Causal/copy_sync_half_200_iter100.txt") as finc, \
                open("/home/yuchen/CppFiles/Causal/copy_syneneg_half_200_iter100.txt") as fine:
            cnt = 0
            for linec, linee in zip(finc, fine):
                cnt +=1
                LogInfo.show_line(cnt, 100000)
                sptc = linec.strip().split()
                spte = linee.strip().split()
                wordc = sptc[0]
                worde = spte[0]
                vecc = map(lambda x: float(x), sptc[1:])
                vece = map(lambda x: float(x), spte[1:])
                self.sync[wordc] = vecc
                self.syne_neg[worde] = vece
        LogInfo.logs("[log] sync/syneneg cause/effect vectors loaded (%d/%d).", len(self.sync), len(self.syne_neg))

        with open("/home/yuchen/CppFiles/Causal/copy_syncneg_half_200_iter100.txt") as finc, \
                open("/home/yuchen/CppFiles/Causal/copy_syne_half_200_iter100.txt") as fine:
            cnt = 0
            for linec, linee in zip(finc, fine):
                cnt +=1
                LogInfo.show_line(cnt, 100000)
                sptc = linec.strip().split()
                spte = linee.strip().split()
                wordc = sptc[0]
                worde = spte[0]
                vecc = map(lambda x: float(x), sptc[1:])
                vece = map(lambda x: float(x), spte[1:])
                self.sync_neg[wordc] = vecc
                self.syne[worde] = vece
        LogInfo.logs("[log] syncneg/syne cause/effect vectors loaded (%d/%d).", len(self.sync_neg), len(self.syne))

        with open("/home/yuchen/data/roc_lem.txt") as fin:
            for i in range(1871):
                raw_sentence = fin.readline().strip() + ' ' + fin.readline().strip() + \
                               ' ' + fin.readline().strip() + ' ' + fin.readline().strip()
                raw_option1 = fin.readline()
                raw_option2 = fin.readline()
                sentence = map(lambda x: x.split(':')[1], raw_sentence.strip().split())
                option1 = map(lambda x: x.split(':')[1], raw_option1.strip().split())
                option2 = map(lambda x: x.split(':')[1], raw_option2.strip().split())
                self.copa_data.append([sentence, option1, option2])
        LogInfo.logs("[log] roc dataset loaded (%d).", len(self.copa_data))

        with open("/home/yuchen/data/roc_label.txt") as fin:
            for line in fin:
                spt = line.strip().split('\t')
                self.copa_ground.append([spt[1], int(spt[2])])
        LogInfo.logs("[log] roc ground truth loaded (%d).", len(self.copa_ground))
        LogInfo.end_track()

    def get_repr(self, sentence, ask4, setting, role):
        """
        :param sentence: 
        :param ask4: 'cause' or 'effect' 
        :param setting: 1: sync/syne_neg, 2: sync_neg/syne, 3: if ask4 cause then sync_neg/syne else sync/syne_neg
        :param role: sentence or option
        :return: 
        """
        ret = np.zeros(200)
        cnt = 0
        if setting == 1:
            if ask4 == 'cause' and role == 'q':
                vec_map = self.syne_neg
            elif ask4 == 'cause' and role == 'o':
                vec_map = self.sync
            elif ask4 == 'effect' and role == 'q':
                vec_map = self.sync
            elif ask4 == 'effect' and role == 'o':
                vec_map = self.syne_neg
        elif setting == 2:
            if ask4 == 'cause' and role == 'q':
                vec_map = self.syne
            elif ask4 == 'cause' and role == 'o':
                vec_map = self.sync_neg
            elif ask4 == 'effect' and role == 'q':
                vec_map = self.sync_neg
            elif ask4 == 'effect' and role == 'o':
                vec_map = self.syne
        elif setting == 3:
            if ask4 == 'cause' and role == 'q':
                vec_map = self.syne
            elif ask4 == 'cause' and role == 'o':
                vec_map = self.sync_neg
            elif ask4 == 'effect' and role == 'q':
                vec_map = self.sync
            elif ask4 == 'effect' and role == 'o':
                vec_map = self.syne_neg

        for word in sentence:
            if word in vec_map:
                ret += np.array(vec_map[word])
                cnt += 1
        if cnt != 0:
            ret /= cnt
        return ret

    @staticmethod
    def get_similarity(vec1, vec2):
        veca = np.array(vec1)
        vecb = np.array(vec2)
        if linalg.norm(veca) == 0 or linalg.norm(vecb) == 0:
            return 0.0
        return dot(veca, vecb.T)/linalg.norm(veca)/linalg.norm(vecb)

    def eval_avg(self, setting=1):
        """
        sentence representation = average of word vectors
        :return: final acc.
        """
        LogInfo.begin_track("Eval on ROC using average word representations using setting %d...", setting)
        correct = 0
        for i in range(0, 1871):
            ask4 = self.copa_ground[i][0]
            sentence, option1, option2 = self.copa_data[i]
            sent_vec = self.get_repr(sentence, ask4, setting, 'q')
            opt1_vec = self.get_repr(option1, ask4, setting, 'o')
            opt2_vec = self.get_repr(option2, ask4, setting, 'o')
            score1 = self.get_similarity(sent_vec, opt1_vec)
            score2 = self.get_similarity(sent_vec, opt2_vec)
            truth = self.copa_ground[i][1]
            if score1 > score2:
                if truth == 1:
                    # LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [T]", i+1, 1, score1, score2, truth)
                    correct += 1
                # else:
                #     LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [F]", i+1, 1, score1, score2, truth)
            else:
                if truth == 2:
                    # LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [T]", i+1, 2, score1, score2, truth)
                    correct += 1
                # else:
                #     LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [F]", i+1, 2, score1, score2, truth)

        LogInfo.logs("[summary] accuracy: %.4f(%d/%d).", float(correct)/1871, correct, 1871)
        LogInfo.end_track()

    def eval_avg_lambda(self, lamb=1.0):
        """
        sentence representation = average of word vectors
        :return: final acc.
        """
        LogInfo.begin_track("Eval on ROC using average word representations using lambda %.2f...", lamb)
        correct = 0
        for i in range(0, 1871):
            ask4 = self.copa_ground[i][0]
            sentence, option1, option2 = self.copa_data[i]
            sent_vec = self.get_repr(sentence, ask4, 1, 'q')
            opt1_vec = self.get_repr(option1, ask4, 1, 'o')
            opt2_vec = self.get_repr(option2, ask4, 1, 'o')
            score1a = self.get_similarity(sent_vec, opt1_vec)
            score2a = self.get_similarity(sent_vec, opt2_vec)

            sent_vec = self.get_repr(sentence, ask4, 2, 'q')
            opt1_vec = self.get_repr(option1, ask4, 2, 'o')
            opt2_vec = self.get_repr(option2, ask4, 2, 'o')
            score1b = self.get_similarity(sent_vec, opt1_vec)
            score2b = self.get_similarity(sent_vec, opt2_vec)

            score1 = (score1a * lamb) + (score1b * (1 - lamb))
            score2 = (score2a * lamb) + (score2b * (1 - lamb))
            # LogInfo.logs("[log] %.4f(%.2f^%.2f*%.2f^%.2f) ||| %.4f(%.2f^%.2f*%.2f^%.2f)",
            #              score1, score1a, lamb, score1b, 1-lamb,
            #              score2, score2a, lamb, score2b, 1-lamb)
            truth = self.copa_ground[i][1]
            if score1 > score2:
                if truth == 1:
                    # LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [T]", i+1, 1, score1, score2, truth)
                    correct += 1
                # else:
                #     LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [F]", i+1, 1, score1, score2, truth)
            else:
                if truth == 2:
                    # LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [T]", i+1, 2, score1, score2, truth)
                    correct += 1
                # else:
                #     LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [F]", i+1, 2, score1, score2, truth)

        LogInfo.logs("[summary] accuracy: %.4f(%d/%d).", float(correct)/1871, correct, 1871)
        LogInfo.end_track()

    def get_vec_map(self, ask4, setting, role):
        """
        :param ask4: 'cause' or 'effect' 
        :param setting: 1: sync/syne_neg, 2: sync_neg/syne, 3: if ask4 cause then sync_neg/syne else sync/syne_neg
        :param role: sentence or option
        :return: vec map
        """

        vec_map = dict()
        if setting == 1:
            if ask4 == 'cause' and role == 'q':
                vec_map = self.syne_neg
            elif ask4 == 'cause' and role == 'o':
                vec_map = self.sync
            elif ask4 == 'effect' and role == 'q':
                vec_map = self.sync
            elif ask4 == 'effect' and role == 'o':
                vec_map = self.syne_neg
        elif setting == 2:
            if ask4 == 'cause' and role == 'q':
                vec_map = self.syne
            elif ask4 == 'cause' and role == 'o':
                vec_map = self.sync_neg
            elif ask4 == 'effect' and role == 'q':
                vec_map = self.sync_neg
            elif ask4 == 'effect' and role == 'o':
                vec_map = self.syne
        elif setting == 3:
            if ask4 == 'cause' and role == 'q':
                vec_map = self.syne
            elif ask4 == 'cause' and role == 'o':
                vec_map = self.sync_neg
            elif ask4 == 'effect' and role == 'q':
                vec_map = self.sync
            elif ask4 == 'effect' and role == 'o':
                vec_map = self.syne_neg

        return vec_map

    def eval_pair(self, setting=1, strategy=1):
        """
        evaluation based on word pairs
        :param setting:
        :param strategy: 1: sum, 2: /T1+T2, 3: /T1*T2
        :return: final acc. 
        """
        LogInfo.begin_track("Eval on ROC using word pairs using setting %d and strategy %d...",
                            setting, strategy)
        correct = 0
        for i in range(0, 1871):
            sentence, option1, option2 = self.copa_data[i]
            ask4 = self.copa_ground[i][0]
            q_vec_map = self.get_vec_map(ask4=ask4, setting=setting, role='q')
            o_vec_map = self.get_vec_map(ask4=ask4, setting=setting, role='o')
            score1 = 0.0
            score2 = 0.0
            for word1 in sentence:
                for word2 in option1:
                    if word1 in q_vec_map and word2 in o_vec_map:
                        score1 += self.get_similarity(q_vec_map[word1], o_vec_map[word2])

            for word1 in sentence:
                for word2 in option2:
                    if word1 in q_vec_map and word2 in o_vec_map:
                        score2 += self.get_similarity(q_vec_map[word1], o_vec_map[word2])

            if strategy == 2:
                score1 /= (len(sentence) + len(option1))
                score2 /= (len(sentence) + len(option2))
            elif strategy == 3:
                score1 /= (len(sentence) * len(option1))
                score2 /= (len(sentence) * len(option2))

            truth = self.copa_ground[i][1]
            if score1 > score2:
                if truth == 1:
                    # LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [T]", i+1, 1, score1, score2, truth)
                    correct += 1
                # else:
                    # LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [F]", i+1, 1, score1, score2, truth)
            else:
                if truth == 2:
                    # LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [T]", i+1, 2, score1, score2, truth)
                    correct += 1
                # else:
                #     LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [F]", i+1, 2, score1, score2, truth)

        LogInfo.logs("[summary] accuracy: %.4f(%d/%d).", float(correct)/1871, correct, 1871)
        LogInfo.end_track()

    def eval_pair_lambda(self, lamb=1.0, strategy=1):
        """
        evaluation based on word pairs
        :param lamb:
        :param strategy: 1: sum, 2: /T1+T2, 3: /T1*T2
        :return: final acc. 
        """
        LogInfo.begin_track("Eval on ROC using word pairs using lambda %.2f and strategy %d...",
                            lamb, strategy)
        correct = 0
        for i in range(0, 1871):
            sentence, option1, option2 = self.copa_data[i]
            ask4 = self.copa_ground[i][0]

            # left
            q_vec_map = self.get_vec_map(ask4=ask4, setting=1, role='q')
            o_vec_map = self.get_vec_map(ask4=ask4, setting=1, role='o')
            score1a = 0.0
            score2a = 0.0
            for word1 in sentence:
                for word2 in option1:
                    if word1 in q_vec_map and word2 in o_vec_map:
                        score1a += self.get_similarity(q_vec_map[word1], o_vec_map[word2])

            for word1 in sentence:
                for word2 in option2:
                    if word1 in q_vec_map and word2 in o_vec_map:
                        score2a += self.get_similarity(q_vec_map[word1], o_vec_map[word2])

            # right
            q_vec_map = self.get_vec_map(ask4=ask4, setting=2, role='q')
            o_vec_map = self.get_vec_map(ask4=ask4, setting=2, role='o')
            score1b = 0.0
            score2b = 0.0
            for word1 in sentence:
                for word2 in option1:
                    if word1 in q_vec_map and word2 in o_vec_map:
                        score1b += self.get_similarity(q_vec_map[word1], o_vec_map[word2])

            for word1 in sentence:
                for word2 in option2:
                    if word1 in q_vec_map and word2 in o_vec_map:
                        score2b += self.get_similarity(q_vec_map[word1], o_vec_map[word2])

            score1 = (score1a * lamb) + (score1b * (1-lamb))
            score2 = (score2a * lamb) + (score2b * (1-lamb))
            if strategy == 2:
                score1 /= (len(sentence) + len(option1))
                score2 /= (len(sentence) + len(option2))
            elif strategy == 3:
                score1 /= (len(sentence) * len(option1))
                score2 /= (len(sentence) * len(option2))

            truth = self.copa_ground[i][1]
            if score1 > score2:
                if truth == 1:
                    # LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [T]", i+1, 1, score1, score2, truth)
                    correct += 1
                # else:
                    # LogInfo.logs("[%d] ret: %d(%.2f>%.2f), truth: %d. [F]", i+1, 1, score1, score2, truth)
            else:
                if truth == 2:
                    # LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [T]", i+1, 2, score1, score2, truth)
                    correct += 1
                # else:
                #     LogInfo.logs("[%d] ret: %d(%.2f<%.2f), truth: %d. [F]", i+1, 2, score1, score2, truth)

        LogInfo.logs("[summary] accuracy: %.4f(%d/%d).", float(correct)/1871, correct, 1871)
        LogInfo.end_track()


if __name__ == '__main__':
    evaluator = ROC_evaluator()
    evaluator.eval_avg(setting=1)
    evaluator.eval_avg(setting=2)
    evaluator.eval_avg(setting=3)

    for j in range(21):
        evaluator.eval_avg_lambda(lamb=j*0.05)

    for i in range(3):
        for j in range(3):
            evaluator.eval_pair(setting=i+1, strategy=j+1)

    for i in range(3):
        for j in range(21):
            evaluator.eval_pair_lambda(lamb=j*0.05, strategy=i+1)

