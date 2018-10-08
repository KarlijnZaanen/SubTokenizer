# coding: utf-8

from __future__ import unicode_literals, division, absolute_import

import io
import sys
import codecs
import argparse
from HTMLParser import HTMLParser
from collections import defaultdict
from subtokenizer.utils import wrap_text_reader, multiprocess, encode_controls, normalize_text, NOBREAK
from subtokenizer.subwords import Subwords, EOS
from subtokenizer.tokenizer import ReTokenizer
from subtokenizer.subtokenizer import SubTokenizer



def learn(args):
    reserved_tokens = None
    if args.reserved:
        f = io.TextIOWrapper(io.BufferedReader(io.FileIO(args.reserved, "r")), encoding='utf-8')
        reserved_tokens = []
        for subtoken in f:
            reserved_tokens.append(subtoken.strip('\n'))
        f.close()
    token_counts = defaultdict(int)

    def tokenize(line):
        line = normalize_text(line.strip('\n'))
        if not args.no_encode_controls:
            line = encode_controls(line)
        return ReTokenizer.tokenize(line)

    if args.processes == 1:
        for l in sys.stdin:
            for token in tokenize(l):
                token_counts[token] += 1
    else:
        for l in multiprocess(tokenize, sys.stdin, processes=args.processes):
            for token in l:
                token_counts[token] += 1
    subdict = SubTokenizer.learn(token_counts, args.size, reserved_tokens=reserved_tokens, min_symbol_count=args.min_symbol_count)
    subdict.save(args.output)


def tokenize(args):
    subwords = None
    if args.subwords:
        subwords = SubTokenizer.load(args.subwords)

    def proc_func(l):
        l = normalize_text(l.strip('\n'))
        if subwords:
            encode_controls = not args.no_encode_controls
            return subwords.tokenize(l, encode_controls=encode_controls, numeric=args.numeric, add_eos=args.add_eos)
        if not args.no_encode_controls:
            line = encode_controls(line)
        tokens = ReTokenizer.tokenize(l)
        if args.add_eos:
            tokens.append(EOS)
        return tokens

    if args.processes == 1:
        for l in sys.stdin:
            tokens = proc_func(l)
            sys.stdout.write(' '.join(tokens))
            sys.stdout.write('\n')
    else:
        for tokens in multiprocess(proc_func, sys.stdin, processes=args.processes):
            sys.stdout.write(' '.join(tokens))
            sys.stdout.write('\n')


def detokenize(HTML_PARSER, args):
    subwords = None
    if args.subwords:
        subwords = SubTokenizer.load(args.subwords)

    def proc_func(l):
        l = l.strip('\n').split(' ')
        if subwords:
            decode = not args.no_decode
            return subwords.detokenize(l, decode=decode, numeric=args.numeric)
        if subwords[-1] == EOS:
            subwords = subwords[:-1]
        text = ReTokenizer.detokenize(tokens)
        if not args.no_decode:
            text = text.replace(NOBREAK, '')
            text = HTML_PARSER.unescape(text)
        return text

    if args.processes == 1:
        for l in sys.stdin:
            line = proc_func(l)
            sys.stdout.write(line)
            sys.stdout.write('\n')
    else:
        for line in multiprocess(proc_func, sys.stdin, processes=args.processes):
            sys.stdout.write(line)
            sys.stdout.write('\n')


def encode(args):
    for line in sys.stdin:
        line = encode_controls(normalize_text(line))
        sys.stdout.write(line)


def decode(HTML_PARSER, args):
    for line in sys.stdin:
        text = text.replace(NOBREAK, '')
        text = HTML_PARSER.unescape(text)
        sys.stdout.write(line)


def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='there are following modes: '
                                       '1) learn 2) tokenize 3) detokenize 4) encode 5) decode', dest="mode")
    parser_learn = subparsers.add_parser('learn', help='learn subtokens from text')
    parser_learn.add_argument('-r', '--reserved',  type=str, help="file with reserved tokens")
    parser_learn.add_argument('-o', '--output', required=True,  type=str, help="subwords dictionary")
    parser_learn.add_argument('-s', '--size', default=30000,  type=int, help="number of subtokens")
    parser_learn.add_argument('-p', '--processes', default=1,  type=int, help="number of tokenizer processes")
    parser_learn.add_argument('-m', '--min_symbol_count', default=1,  type=int, help="minimal character count to be in alphabet")
    parser_learn.add_argument('-c', '--no_encode_controls', action='store_true', help="do not encode control symbols")
    parser_tokenize = subparsers.add_parser('tokenize', help='tokenize text')
    parser_tokenize.add_argument('-s', '--subwords',  default=None, type=str, help="subwords dictionary")
    parser_tokenize.add_argument('-n', '--numeric',  action='store_true', help="numeric output")
    parser_tokenize.add_argument('-p', '--processes', default=1,  type=int, help="number of tokenizer processes") 
    parser_tokenize.add_argument('-e', '--add_eos', action='store_true', help="add end of line")
    parser_tokenize.add_argument('-c', '--no_encode_controls', action='store_true', help="do not encode control symbols")
    parser_detokenize = subparsers.add_parser('detokenize', help='restore tokenized text')
    parser_detokenize.add_argument('-s', '--subwords',  default=None, type=str, help="subwords dictionary")
    parser_detokenize.add_argument('-n', '--numeric',  action='store_true', help="numeric output")
    parser_detokenize.add_argument('-p', '--processes', default=1,  type=int, help="number of tokenizer processes")
    parser_detokenize.add_argument('-d', '--no_decode', action='store_true', help="do not decode encoded symbols")
    parser_decode = subparsers.add_parser('decode', help='decoding encoded symbols')
    parser_encode = subparsers.add_parser('encode', help='unicode normalization and encodeing contrlos symbols')
    return parser


def main():
    HTML_PARSER = HTMLParser()
    sys.stdin = wrap_text_reader(sys.stdin, encoding='utf-8')
    if sys.version_info < (3, 0):
        sys.stderr = codecs.getwriter('UTF-8')(sys.stderr)
        sys.stdout = codecs.getwriter('UTF-8')(sys.stdout)
    else:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True, line_buffering=True)

    parser = get_parser()
    args = parser.parse_args()
    if args.mode == 'learn':
        learn(args)
    elif args.mode == 'tokenize':
        tokenize(args)
    elif args.mode == 'detokenize':
        detokenize(HTML_PARSER, args)
    elif args.mode == 'decode':
        decode(HTML_PARSER, args)
    elif args.mode == 'encode':
        encode(args)
    else:
        print('unknown mode')
