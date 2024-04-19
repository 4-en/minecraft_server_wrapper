

# Cyclic list
# a list with a maximum length, when the list is full, the oldest element will be removed
# internally, use a fixed size list to store the elements
# keep track of the current index to insert the next element

class CyclicList:
    def __init__(self, max_length):
        self.max_length = max_length
        self.list = [None] * max_length
        self.index = 0 # the index to insert the next element
        self.last_index = -1 # the last index that contains an element

    def append(self, element):
        self.list[self.index] = element
        self.index = (self.index + 1) % self.max_length

    def as_list(self):
        if self.last_index == -1:
            return []
        if self.last_index < self.max_length - 1:
            return self.list[:self.last_index + 1]
        return self.list[self.index:] + self.list[:self.index]
    
    def __len__(self):
        return self.last_index + 1
    
    def __getitem__(self, index):
        if index < 0 or index > self.last_index:
            raise IndexError("Index out of range")
        
        return self.as_list()[index]
    
    def __iter__(self):
        return iter(self.as_list())
    
    def __repr__(self):
        return str(self.as_list())
    
    def __str__(self):
        return str(self.as_list())
    
    def __bool__(self):
        return self.last_index != -1
    
    def __contains__(self, element):
        return element in self.as_list()
    
    def __eq__(self, other):
        return self.as_list() == other
    
    def __ne__(self, other):
        return self.as_list() != other
