import chromadb
import csv

class VectorDatabase:
    def __init__(self, path="./chroma_db", collection_name="recipes"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def load_data(self, csv_file="full_dataset.csv", batch_size=5000, limit=None):
        batch_documents = []
        batch_metadatas = []
        batch_ids = []
        
        with open(csv_file, "r") as f:
            reader = csv.reader(f)
        
            # Skip header
            next(reader)
        
            record_count = 0
            batch_num = 0
        
            for record in reader:
                recipe_id = record[0]
                title = record[1]
                ingredients = record[2]
                steps = record[3]
        
                document = f"Title: {title}\nIngredients: {ingredients}\n\nSteps: {steps}"
                metadata = {"title": title, "ingredients": ingredients, "steps": steps}
        
                batch_documents.append(document)
                batch_metadatas.append(metadata)
                batch_ids.append(recipe_id)
        
                record_count += 1
        
                if record_count % batch_size == 0:
                    batch_num += 1
                    print(f"--- Adding batch {batch_num} with {batch_size} records... ---")
        
                    self.collection.add(
                            documents=batch_documents,
                            metadatas=batch_metadatas,
                            ids=batch_ids
                            )
        
                    batch_documents = []
                    batch_metadatas = []
                    batch_ids = []
                    print(f"Batch {batch_num} added successfully.")

                if limit and record_count >= limit:
                    break
        
        if batch_documents:
            batch_num += 1
            final_batch_size = len(batch_documents)
            print(f"\n--- Adding final batch {batch_num} with {final_batch_size} records... ---")

            self.collection.add(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                    )
            print(f"Final batch {batch_num} added successfully.")

    def search(self, queries=[], where=None, where_document=None, n_results=10):
        results = self.collection.query(
                query_texts=queries,
                where=where,
                where_document=where_document,
                n_results=n_results
                )
        return results
