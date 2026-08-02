from memory.query import MemoryQuery

query = MemoryQuery()

tests = [
    "What's my name?",
    "What is my favorite language?",
    "What is my favourite color?",
    "Hello"
]

for sentence in tests:
    print(sentence)
    print(query.find_key(sentence))
    print("-" * 30)