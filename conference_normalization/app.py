from flask import Flask, render_template, request, jsonify
import os
from itertools import combinations

app = Flask(__name__)

def find_closure(attributes, fds, X):
    """Find closure of attribute set X under given functional dependencies"""
    closure = set(X)
    changed = True
    while changed:
        changed = False
        for fd in fds:
            if set(fd['left']).issubset(closure) and not set(fd['right']).issubset(closure):
                closure.update(fd['right'])
                changed = True
    return closure

def find_candidate_keys(attributes, fds):
    """Find all candidate keys for the relation"""
    candidate_keys = []
    # Check all possible combinations of attributes
    for i in range(1, len(attributes)+1):
        for combo in combinations(attributes, i):
            combo_set = set(combo)
            closure = find_closure(attributes, fds, combo_set)
            if closure == set(attributes):
                # Check for minimality
                is_minimal = True
                for key in candidate_keys:
                    if set(key).issubset(combo_set):
                        is_minimal = False
                        break
                if is_minimal:
                    candidate_keys.append(combo)
    return candidate_keys

def is_partial_dependency(fd, candidate_keys):
    """Check if a functional dependency is a partial dependency"""
    for key in candidate_keys:
        if set(fd['left']).issubset(key) and set(fd['left']) != set(key):
            return True
    return False

def is_transitive_dependency(fd, candidate_keys):
    """Check if a functional dependency is a transitive dependency"""
    for key in candidate_keys:
        if (not set(fd['left']).issuperset(key) and 
            not any(attr in key for attr in fd['right'])):
            return True
    return False

def violates_bcnf(fd, candidate_keys):
    """Check if a functional dependency violates BCNF"""
    for key in candidate_keys:
        if set(fd['left']).issuperset(key):
            return False
    return True

def normalize_to_1nf(attributes, fds):
    """Convert to 1NF by handling multi-valued attributes"""
    # For conference system, we handle author lists
    if any(attr.startswith('author_') for attr in attributes):
        # Split into papers and authors
        papers_attrs = [a for a in attributes if not a.startswith('author_')]
        authors_attrs = ['paper_id', 'author_position', 'author_name', 
                        'author_email', 'author_affiliation']
        
        # Update FDs for the new structure
        new_fds = []
        for fd in fds:
            if (any(a.startswith('author_') for a in fd['left']) or
                any(a.startswith('author_') for a in fd['right'])):
                new_left = [a.replace('author_', '') if a.startswith('author_') else a for a in fd['left']]
                new_right = [a.replace('author_', '') if a.startswith('author_') else a for a in fd['right']]
                new_fds.append({'left': new_left, 'right': new_right})
        
        return [
            {'name': 'Papers', 'attributes': papers_attrs, 'fds': [fd for fd in fds if not any(a.startswith('author_') for a in fd['left'] + fd['right'])]},
            {'name': 'Paper_Authors', 'attributes': authors_attrs, 'fds': new_fds}
        ]
    return [{'name': 'Original', 'attributes': attributes, 'fds': fds}]

def normalize_to_2nf(relations):
    """Convert relations to 2NF by removing partial dependencies"""
    new_relations = []
    for rel in relations:
        candidate_keys = find_candidate_keys(rel['attributes'], rel['fds'])
        partial_deps = [fd for fd in rel['fds'] if is_partial_dependency(fd, candidate_keys)]
        
        if not partial_deps:
            new_relations.append(rel)
            continue
        
        # Decompose for each partial dependency
        for fd in partial_deps:
            # Create new relation with the FD
            new_attrs = list(set(fd['left'] + fd['right']))
            new_fds = [fd for fd in rel['fds'] 
                      if set(fd['left']).issubset(new_attrs)]
            new_relations.append({
                'name': f"{rel['name']}_{'_'.join(fd['left'])}",
                'attributes': new_attrs,
                'fds': new_fds
            })
            
            # Update original relation
            rel['attributes'] = [a for a in rel['attributes'] if a not in fd['right'] or a in fd['left']]
            rel['fds'] = [fd for fd in rel['fds'] if not set(fd['left']).issubset(new_attrs)]
        
        new_relations.append(rel)
    return new_relations

def normalize_to_3nf(relations):
    """Convert relations to 3NF by removing transitive dependencies"""
    new_relations = []
    for rel in relations:
        candidate_keys = find_candidate_keys(rel['attributes'], rel['fds'])
        transitive_deps = [fd for fd in rel['fds'] 
                          if is_transitive_dependency(fd, candidate_keys)]
        
        if not transitive_deps:
            new_relations.append(rel)
            continue
        
        for fd in transitive_deps:
            # Create new relation with the transitive FD
            new_attrs = list(set(fd['left'] + fd['right']))
            new_fds = [fd for fd in rel['fds'] 
                      if set(fd['left']).issubset(new_attrs)]
            new_relations.append({
                'name': f"{rel['name']}_{'_'.join(fd['left'])}",
                'attributes': new_attrs,
                'fds': new_fds
            })
            
            # Update original relation
            rel['attributes'] = [a for a in rel['attributes'] if a not in fd['right'] or a in fd['left']]
            rel['fds'] = [fd for fd in rel['fds'] if not set(fd['left']).issubset(new_attrs)]
        
        new_relations.append(rel)
    return new_relations

def normalize_to_bcnf(relations):
    """Convert relations to BCNF"""
    new_relations = []
    for rel in relations:
        candidate_keys = find_candidate_keys(rel['attributes'], rel['fds'])
        violating_fds = [fd for fd in rel['fds'] 
                        if violates_bcnf(fd, candidate_keys)]
        
        if not violating_fds:
            new_relations.append(rel)
            continue
        
        for fd in violating_fds:
            # Create new relation with the violating FD
            new_attrs = list(set(fd['left'] + fd['right']))
            new_fds = [fd for fd in rel['fds'] 
                      if set(fd['left']).issubset(new_attrs)]
            new_relations.append({
                'name': f"{rel['name']}_{'_'.join(fd['left'])}",
                'attributes': new_attrs,
                'fds': new_fds
            })
            
            # Update original relation
            rel['attributes'] = [a for a in rel['attributes'] if a not in fd['right'] or a in fd['left']]
            rel['fds'] = [fd for fd in rel['fds'] if not set(fd['left']).issubset(new_attrs)]
        
        new_relations.append(rel)
    return new_relations

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/normalize', methods=['POST'])
def normalize():
    data = request.json
    
    try:
        # Handle both string and list input for attributes
        if isinstance(data['attributes'], str):
            attributes = [a.strip() for a in data['attributes'].split(',') if a.strip()]
        else:  # Assume it's already a list
            attributes = [a.strip() for a in data['attributes'] if a.strip()]
        
        # Process functional dependencies
        fds = []
        for fd in data['fds']:
            left = fd['left'] if isinstance(fd['left'], list) else [x.strip() for x in str(fd['left']).split(',') if x.strip()]
            right = fd['right'] if isinstance(fd['right'], list) else [x.strip() for x in str(fd['right']).split(',') if x.strip()]
            if left and right:  # Only add if both sides have values
                fds.append({'left': left, 'right': right})
        
        # Perform normalization
        relations_1nf = normalize_to_1nf(attributes, fds)
        relations_2nf = normalize_to_2nf(relations_1nf)
        relations_3nf = normalize_to_3nf(relations_2nf)
        relations_bcnf = normalize_to_bcnf(relations_3nf)
        
        # Prepare results
        result = {
            '1NF': {
                'description': 'First Normal Form: Split multi-valued attributes',
                'tables': [{'name': r['name'], 'attributes': r['attributes']} 
                          for r in relations_1nf]
            },
            '2NF': {
                'description': 'Second Normal Form: Removed partial dependencies',
                'tables': [{'name': r['name'], 'attributes': r['attributes']} 
                          for r in relations_2nf]
            },
            '3NF': {
                'description': 'Third Normal Form: Removed transitive dependencies',
                'tables': [{'name': r['name'], 'attributes': r['attributes']} 
                          for r in relations_3nf]
            },
            'BCNF': {
                'description': 'Boyce-Codd Normal Form: All FDs have superkeys on left',
                'tables': [{'name': r['name'], 'attributes': r['attributes']} 
                          for r in relations_bcnf]
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True)