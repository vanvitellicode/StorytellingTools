class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

    def nadd(self, data):
        n = Node(data)
        self.prev = n
        n.next = self
        return n

    def ndel(self):
        if self is not None:
            if self.prev is not None:
                self.prev.next = self.next
            if  self.next is not None:
                self.next.prev = self.prev
            if self.next is None:
                print("tail")
                self.prev.next = None
            if self.prev is None and self.next is None:
                print("empty")
        else:
            print("self None")

    def nget(self):
        return self.data

    def is_last(self):
        return (self.next is None and self.prev is None)

    def is_last_next(self):
        return (self.next is None)


if __name__ == "__main__":
    print('asdf')
    h = Node(1)
    h= h.nadd(2)
    h= h.nadd(3)
    h= h.nadd(4)
    print(h.nget())
    print(h.next.nget())
    print(h.next.next.nget())
    print(h.next.next.next.nget())

    h.next.ndel()
    print(h.nget())
    print(h.next.nget())
    print(h.next.next.nget())
    print(h.next.next)
    print(h.next.prev)
    print(h)

    h.next.ndel()
    print(h.nget())
    print(h.next.nget())
    print(h.next.next)
    print(h.next.prev)
    print(h)
    h.next.ndel()
    print(h.next)
    print(h.prev)
