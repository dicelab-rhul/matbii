from matbii.utils import MultiTaskLoader

if __name__ == "__main__":
    loader = MultiTaskLoader()
    for name, data in loader:
        print(name, repr(data[:100]), "...")
    print(loader.get_index())
