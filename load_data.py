from db import VectorDatabase

VectorDatabase().load_data()

print(VectorDatabase().search("thai main course", n_results=5))
