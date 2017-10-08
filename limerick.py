#!/usr/bin/env python
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit

# Use word_tokenize to split raw text into words
from string import punctuation

import nltk
from nltk.tokenize import word_tokenize

scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')

def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)



class LimerickDetector:

    def __init__(self):
        """
        Initializes the object to have a pronunciation dictionary available
        """
        self._pronunciations = nltk.corpus.cmudict.dict()
        #print  self._pronunciations


    def num_syllables(self, word):
        """
        Returns the number of syllables in a word.  If there's more than one
        pronunciation, take the shorter one.  If there is no entry in the
        dictionary, return 1.
        """
        pron = self._pronunciations
        try:
            word_prons = pron[word]
            print word_prons
            if (len(word_prons) > 1):
                min = self.get_tot_syllb(pron[word][0])
                for word_pron in word_prons[1:]:
                    cur = self.get_tot_syllb(word_pron)
                    print cur
                    if (cur < min):
                        min = cur
                return min

            elif (len(word_prons) == 1):
                word_pron = pron[word][0]
                return self.get_tot_syllb(word_pron)
        except:
            return 1

        # TODO: provide an implementation!

        return 1

    def is_syllable(self,char):
        return (str(char[-1]).isdigit())

    def get_tot_syllb(self,wrd):
        #print wrd
        tot_syllables = 0
        for x in wrd:
            if (self.is_syllable(x)):
                tot_syllables += 1
        return tot_syllables



    def rhymes(self, a, b):
        """
        Returns True if two words (represented as lower-case strings) rhyme,
        False otherwise.
        """
        pron = self._pronunciations
        try:
            aprons = pron[a]
            bprons = pron[b]
            #print "\n"

            finalres = False
            #print range(len(aprons))
            #print range(len(bprons))
            for i in range(len(aprons)):
                for j in range(len(bprons)):
                    apron = aprons[i]
                    bpron = bprons[j]
                    #print apron, "." ,bpron
                    finalres = self.compare(apron,bpron)
                    #print finalres
                    if (finalres):
                        break
                if (finalres):
                    break

            # TODO: provide an implementation!

            print "Final :", finalres
            return finalres

        except:
            print "word not in dictionary"
            return False

    def compare(self,apron,bpron):
        acounter = 0
        for char in apron:
            if (self.is_syllable(char)):
                break
            acounter += 1
        #print apron
        #print acounter
        astripped = apron[acounter:]
        #print astripped
        asize = len(astripped)
        #print "asize " + str(asize)
        #print "\n"

        bcounter = 0
        for char in bpron:
            if (self.is_syllable(char)):
                break
            bcounter += 1
        # print bpron
        # print bcounter
        bstripped = bpron[bcounter:]
        #print bstripped
        bsize = len(bstripped)
        #print "bsize " + str(bsize)

        res = self.compare_stripped(astripped, bstripped, asize, bsize)
        return res
        #print "\n"


    def compare_stripped(self,astripped,bstripped,asize,bsize):
        #print "\n"
        res = False
        if(asize==bsize):
            # print "case1 a==b"
            # print "comparing", astripped, "and", bstripped
            res = astripped==bstripped
            #print res
            #print "\n"
            return res

        if(asize>bsize):
            # print "case2 a>b"
            # print "comparing", astripped[-bsize:], "and", bstripped
            res = astripped[-bsize:]==bstripped
            #print res
            # print "\n"
            return res

        if(asize<bsize):
            # print "case3 a<b"
            # print "comparing", astripped, "and", bstripped[-asize:]
            res = astripped==bstripped[-asize:]
            #print res
            #print "\n"
            return res



    def is_limerick(self, text):
        """
        Takes text where lines are separated by newline characters.  Returns
        True if the text is a limerick, False otherwise.

        A limerick is defined as a poem with the form AABBA, where the A lines
        rhyme with each other, the B lines rhyme with each other, and the A lines do not
        rhyme with the B lines.


        Additionally, the following syllable constraints should be observed:
          * No two A lines should differ in their number of syllables by more than two.
          * The B lines should differ in their number of syllables by no more than two.
          * Each of the B lines should have fewer syllables than each of the A lines.
          * No line should have fewer than 4 syllables

        (English professors may disagree with this definition, but that's what
        we're using here.)


        """
        # words = nltk.tokenize.word_tokenize(text)
        # print words
        lines = text.lower().strip().splitlines()
        str_list = filter(None, lines)

        if(len(str_list)!=5):
            print "\nnot limerick cuz of 5 line constraint"
            return False

        endwords=[]
        num_syll = []
        for line in str_list:
            for ch in [',','?',':','!','.',';','\"','#','$','%','&','(',')','*','+','-','/','<','>','\\','=','@','[',']','^','_','~','`','|','{','}']:
             if (ch in line):
                line = line.replace(ch,"")

            words = nltk.tokenize.word_tokenize(line)
            #words = self.apostrophe_tokenize(line)
            print words
            endwords.append(words[-1])
            tot = 0
            for word in words:
               tot+=self.get_tot_word_syllable(word)
            num_syll.append(tot)
            if(tot<4):
                print "\nnot limerick cuz of 4 sylb constraint on a line"
                return False

        print num_syll
        anum_syll = num_syll[0:2]
        anum_syll.append(num_syll[-1])

        bnum_syll = num_syll[2:4]


        alist = endwords[0:2]
        alist.append(endwords[-1])
        print alist

        blist = endwords[2:4]
        print blist

        resa = False
        for i in range(0,2):
            for j in range(i+1,3):
                print alist[i], alist[j]
                resa = self.rhymes(alist[i],alist[j])
                if(not resa):
                    print "\nalines not rhyming with each other"
                    return False

                absa = abs(anum_syll[i] - anum_syll[j])
                if (absa > 2):
                    print "\nalines differ by more than 2 syllables"
                    return False

        print "\n"
        print blist[0], blist[1]
        resb = self.rhymes(blist[0],blist[1])
        if (not resb):
            print "\nblines not rhyming with each other"
            return False

        absb = abs(bnum_syll[0]-bnum_syll[1])
        if (absb > 2):
            print "\nblines differ by more than 2 syllables"
            return False

        print "\n"
        resab = False
        for i in range(len(alist)):
            for j in range(len(blist)):
                print alist[i], blist[j]

                if (bnum_syll[j]>anum_syll[i]):
                    print "\n blines have more syllables than alines"
                    return False

                resab = self.rhymes(alist[i], blist[j])
                if (resab):
                    print "\nablines rhyming with each other"
                    return False


        # TODO: provide an implementation!
        print "\nall rhyming constraints satisified"
        return True

    def get_tot_word_syllable(self,word):
        pron = self._pronunciations
        try:
            word_prons = pron[word]
            #print word_prons
            if (len(word_prons) > 1):
                min = self.get_tot_syllb(word_prons[0])
                for word_pron in word_prons[1:]:
                    cur = self.get_tot_syllb(word_pron)
                    #print cur
                    if (cur < min):
                        min = cur
                return min

            elif (len(word_prons) == 1):
                word_pron = word_prons[0]
                return self.get_tot_syllb(word_pron)

        except:
            return 1


    def apostrophe_tokenize(self,line):
        pron = self._pronunciations

        words = line.split()
        proc_list = []
        for x in words:
            if (not(x.strip()=='')):
                proc_list.append(x)

        return proc_list


    def guess_syllables(self,word):
        count = 0;
        vowels = ['a','e','i','o','u','y']
        for x in word:
            if(x.lower() in vowels ):
                count+=1
        vow = count
        if len(word)>=2:
            if 'e'==word[-1:]:
                count-=1
            if 'y'== word[1:]:
                count-=1
            if ('ed' in word):
                if (not ('ded' in word)) and (not ('ted' in word)):
                    count -= 1
            for x in vowels:
                for y in vowels:
                    vowel_pair = x+y
                    if(vowel_pair in word and (not(vowel_pair=='ee'))):
                        count-=1
        if count<=0:
            return vow
        return count



# The code below should not need to be modified
def main():
  parser = argparse.ArgumentParser(description="limerick detector. Given a file containing a poem, indicate whether that poem is a limerick or not",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')

  ld = LimerickDetector()
  lines = ''.join(infile.readlines())
  outfile.write("{}\n-----------\n{}\n".format(lines.strip(), ld.is_limerick(lines)))

if __name__ == '__main__':
    main()
    # ld = LimerickDetector()
    # x= ld.guess_syllables("boolean")
    # print x

    #x = ld.num_syllables("who's")
    #print x

    # x = ld.rhymes("fire","all")
    # print x

#     x = ld.is_limerick("""a woman whose friends called a prude
# on a lark when bathing all nude
# saw a man come conspire
# and unless we are fire
# you expected this line to be lewd""")
#     print x
