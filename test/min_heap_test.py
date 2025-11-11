from utils.min_heap import RepeatMessageHeap

heap = RepeatMessageHeap(capacity=10, threshold=3)

print("min heap test start")

print(heap.add(912579570, "1"))  # False (1次)
print(heap.add(912579570, "1"))  # False (2次)
print(heap.add(912579570, "1"))  # True (3次，触发！)
print(heap.add(912579570, "1"))  # False (清空后重新计数)
