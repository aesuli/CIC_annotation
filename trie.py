from collections import defaultdict


class TrieNode:
    def __init__(self):
        self._children = defaultdict(TrieNode)
        self._leaf_count = 0
        self._prefix_count = 0

    def insert(self, sequence):
        if len(sequence) == 0:
            self._leaf_count += 1
        else:
            self._prefix_count += 1
            self._children[sequence[0]].insert(sequence[1:])

    def prefix_matches(self,sequence, prefix = None):
        if prefix is None:
            prefix = []
        if self._leaf_count > 0:
            yield (prefix, self._leaf_count)
        if len(sequence)>0:
            item = sequence[0]
            node = self._children.get(item)
            if node:
                for matches in node.prefix_matches(sequence[1:], prefix+[item]):
                    yield matches

    def __repr__(self):
        return f'TrieNone(_leaf_count={self._leaf_count}, _prefix_count={self._prefix_count}, _children={self._children})'


class Trie:
    def __init__(self, sequences=None):
        self._root = TrieNode()
        if sequences:
            for sequence in sequences:
                self.insert(sequence)

    def insert(self, sequence: list):
        if len(sequence) > 0:
            self._root.insert(sequence)

    def prefix_matches(self,sequence):
        if len(sequence)==0:
            return None
        return self._root.prefix_matches(sequence)


    def __repr__(self):
        return f'Trie(_root={self._root.__repr__()})'


if __name__ == '__main__':
    trie = Trie()
    trie.insert([])
    trie.insert(['a'])
    trie.insert(['a','b'])
    trie.insert(['a','b','c'])
    trie.insert(['a','b','c','d'])
    trie.insert(['a','b','c','e'])
    trie.insert(['a'])
    trie.insert(['a'])

    print(trie)

    sequence = ['a','b','c','e','a','b','x','b','c']
    for i in range(len(sequence)):
        print(i,list(trie.prefix_matches(sequence[i:])))