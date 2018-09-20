# SubTokenizer
Subwords tokenizer based on google code from tensor2tensor

Standalone subwords tokenizer from https://github.com/tensorflow/tensor2tensor/blob/master/tensor2tensor/data_generators/text_encoder.py

Install:
```bash
 pip install git+https://github.com/kovalevfm/SubTokenizer.git
```

Usage:
```bash
cat text_file.txt | subtokenizer learn -o bpe.file -s 1000 -r reserved_tokens.txt
cat text_file.txt | subtokenizer learn -s bpe.file > tokenized_file.txt
```


