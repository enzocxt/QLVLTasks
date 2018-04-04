from __future__ import absolute_import

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class Sentence(object):
    def __init__(self, xml_text):
        root = ET.fromstring(xml_text)
        sentence_tag = 'sentence'
        sentence_item = self.find_rec(root, sentence_tag)
        sentence = sentence_item.tail.strip()
        # list of items
        self.items = self.parse_sentence(sentence)

    @classmethod
    def find(cls, node, element):
        item = cls.find_rec(node, element)
        return item

    @classmethod
    def find_rec(cls, node, element):
        res = node.find(element)
        if res is None:
            for item in node:
                res = Sentence.find_rec(item, element)
        return res

    def parse_sentence(self, sentence):
        # check every line in sentence
        # if line does not start with a digit number (current lemma id)
        # it should be the last line with '!'
        lines = sentence.split('\n')
        lines = filter(lambda x: x[0].isdigit(), map(lambda x: x.strip(), lines))
        return lines
