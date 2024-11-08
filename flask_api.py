
from dbRetriever.dbRetriever import DBRetriever
from flask import Flask, request, jsonify
from typing import List, Dict
import json
from flask_cors import CORS
from dbRetriever.outputJsonifier import clean_incomplete_and_trailing_comma

app = Flask(__name__)
CORS(app, origins=["*"]) 
db_file = 'products_84000.db'
table_name = 'products'
retriever = DBRetriever(db_file, table_name)

with open("data_84000_conflationV2_Final.json", "r") as f:
    products: Dict[str, Dict[str, List[str]]] = json.loads(f.read())

@app.route('/find_products', methods=['POST'])
def find_products():
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({'error': 'Invalid input. Please provide input as string.'}), 400
    
    input_pairs: List[List[str]] = clean_incomplete_and_trailing_comma(data['input'])
    print(input_pairs)
    min_match_threshold: int = data.get('min_match_threshold', 1)
    
    try:
        new_input_pairs, matched_products = retriever.main(input_pairs, len(input_pairs)-1)
        images: List[str] = []
        for i in matched_products:
            # images.extend(products[i[0]]['Image_url'][:2])
            images.append({
                "url": products[i[0]]['Item_url'][0],
                "img_src": products[i[0]]['Image_url'][0],
                "title": products[i[0]]['Display_title'][0]
            })
        return jsonify({
            'input': new_input_pairs,
            'matched_products': matched_products,
            'images': images
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='164.52.194.185', port=5000,debug=True)
