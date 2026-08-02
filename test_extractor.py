from memory.extractor import MemoryExtractor

extractor = MemoryExtractor()

tests = [
    "My name is Vardhan",
    "My favorite language is Python",
    "My favourite color is Blue",
    "Hello there"
]

for sentence in tests:
    print(sentence)
    print(extractor.extract(sentence))
    print("-" * 30)