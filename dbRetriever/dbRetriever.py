
import sqlite3

from typing import List, Set, Dict, Tuple
import itertools

from sentence_transformers import SentenceTransformer
from torch import Tensor, cosine_similarity
import numpy as np

embedding_cache: Dict[str, Tensor] = {}

class DBRetriever(object):
    def __init__(self, db_file: str, table_name: str, model: str='all-MiniLM-L6-v2'):
        # self.conn = self.connect_to_db(db_file)
        self.db_file = db_file
        self.table_name = table_name
        self.model = SentenceTransformer(model)
        self.model.eval()
        
        self.all_attributes = self.fetch_column_names()
        self.cache_embeddings(self.all_attributes)
        
    def connect_to_db(self):
        return sqlite3.connect(self.db_file)
    
    def fetch_column_names(self):
        with self.connect_to_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({self.table_name});")
            columns = cursor.fetchall()
            
            column_names = [col[1] for col in columns if col[1] != '_id']
        
        return column_names
    
    def cache_embeddings(self, attributes: List[str]):
        global embedding_cache
        for attr in attributes:
            if attr not in embedding_cache:
                embedding_cache[attr] = self.model.encode(attr, convert_to_tensor=True).cpu()
                
    def find_closest_attribute(self, input_attr: str, sim_threshold: float=0.7):
        global embedding_cache
        
        input_embeddings = self.model.encode(input_attr, convert_to_tensor=True).cpu()
        
        similarities: List[float] = []
        for attr in self.all_attributes:
            attr_embedding = embedding_cache[attr]
            similarity = cosine_similarity(input_embeddings.reshape([1, 384]), attr_embedding.reshape([1, 384])).item()
            similarities.append(similarity)
            
        max_sim_idx = np.argmax(similarities)
        max_sim_value = similarities[max_sim_idx]
        if max_sim_value >= sim_threshold:
            return self.all_attributes[max_sim_idx], max_sim_value
        else:
            return None, None
        
    def clean_the_attrs(self, input_pairs: List[List[str]]):
        new_input_pairs: List[List[str]] = []
        
        for attr, v in input_pairs:
            closest_attr, _ = self.find_closest_attribute(attr)
            if closest_attr:
                new_input_pairs.append([closest_attr, v])
        
        return new_input_pairs
    
    def construct_sql_query(self, input_pairs: List[List[str]], min_match_threshold: int=1):
        cte_queries: List[str] = []
        num_conditions = len(input_pairs)
        for match_count in range(num_conditions, min_match_threshold-1, -1):
            for i, combination in enumerate(itertools.combinations(input_pairs, match_count)):
                sub_conditions = [
                    f"LOWER({input_attr}) LIKE LOWER('%{input_value}%')" for input_attr, input_value in combination
                ]
                
                where_clause = " AND ".join(sub_conditions)
                cte_queries.append(f"match_{match_count}_{i} AS (SELECT _id, {match_count} AS match_count FROM {self.table_name} WHERE {where_clause})")
        
        with_clause = ",\n".join(cte_queries)
        unioned_matches = "\nUNION ALL\n".join(
            f"SELECT * FROM match_{match_count}_{i}"
            for match_count in range(num_conditions, min_match_threshold-1, -1)
            for i, _ in enumerate(itertools.combinations(input_pairs, match_count))
        )
        final_query = (
            f"WITH {with_clause}\n"
            "SELECT _id, match_count FROM (\n" +
            unioned_matches +
            ") ORDER BY match_count DESC;"
        )
        
        return final_query
    
    def fetch_matched_products(self, query: str):
        with self.connect_to_db() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
        
        seen_ids: Set[str] = set()
        filtered_results: List[Tuple[str, int]] = []
        for row in results:
            product_id = row[0]
            if product_id not in seen_ids:
                filtered_results.append(row)
                seen_ids.add(product_id)
        
        return filtered_results
    
    def main(self, input_pairs: List[List[str]], min_match_threshold: int):
        
        new_input_pairs = self.clean_the_attrs(input_pairs)
        query = self.construct_sql_query(new_input_pairs, min_match_threshold)
        matched_products = self.fetch_matched_products(query)
        
        return new_input_pairs, matched_products
    