from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

@app.route('/api/normalize', methods=['POST'])
def normalize():
    data = request.json
    
    # Extract input
    relation_name = data['relationName']
    attributes = [a.strip() for a in data['attributes'].split(',')]
    fds = [{'left': fd['left'].split(','), 'right': fd['right'].split(',')} 
           for fd in data['fds']]
    
    # Perform normalization
    result = perform_normalization(relation_name, attributes, fds)
    
    return jsonify(result)

def perform_normalization(relation_name, attributes, fds):
    """Python implementation of normalization steps"""
    # 1NF - Handle composite attributes
    relations_1nf = []
    if 'author_names' in attributes:
        papers_attrs = [a for a in attributes if not a.startswith('author_')]
        authors_attrs = ['paper_id', 'author_position', 'author_name', 'author_email', 'author_affiliation']
        
        relations_1nf.extend([
            {'name': 'PAPERS', 'attributes': papers_attrs},
            {'name': 'PAPER_AUTHORS', 'attributes': authors_attrs}
        ])
    else:
        relations_1nf.append({'name': relation_name, 'attributes': attributes})
    
    # 2NF - Remove partial dependencies (implementation omitted for brevity)
    relations_2nf = normalize_to_2nf(relations_1nf, fds)
    
    # 3NF - Remove transitive dependencies
    relations_3nf = normalize_to_3nf(relations_2nf, fds)
    
    # BCNF - Final normalization
    relations_bcnf = normalize_to_bcnf(relations_3nf, fds)
    
    return {
        'steps': [
            {'name': '1NF', 'relations': relations_1nf},
            {'name': '2NF', 'relations': relations_2nf},
            {'name': '3NF', 'relations': relations_3nf},
            {'name': 'BCNF', 'relations': relations_bcnf}
        ]
    }

if __name__ == '__main__':
    app.run(debug=True)