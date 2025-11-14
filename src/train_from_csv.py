"""
Train chatbot model from CSV dataset
CSV format: question,intent,answer
"""
import pandas as pd
import json
from intent_classifier import IntentClassifier

def csv_to_intents(csv_path):
    """Convert CSV dataset to intents.json format"""
    df = pd.read_csv(csv_path)
    
    intents_dict = {}
    for _, row in df.iterrows():
        intent = row['intent']
        question = row['question']
        
        if intent not in intents_dict:
            intents_dict[intent] = {
                'tag': intent,
                'patterns': [],
                'responses': []
            }
        
        intents_dict[intent]['patterns'].append(question)
        if 'answer' in row and row['answer'] not in intents_dict[intent]['responses']:
            intents_dict[intent]['responses'].append(row['answer'])
    
    return {'intents': list(intents_dict.values())}

def train_from_csv(csv_path, output_json='data/intents_from_csv.json'):
    """Train model from CSV dataset"""
    print(f"Loading dataset from {csv_path}...")
    
    # Convert CSV to intents format
    intents_data = csv_to_intents(csv_path)
    
    # Save to JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(intents_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Converted to {output_json}")
    print(f"Total intents: {len(intents_data['intents'])}")
    
    # Train model
    classifier = IntentClassifier(intents_file=output_json)
    classifier.train()
    print("✓ Model trained successfully!")

if __name__ == '__main__':
    # Example usage:
    # Create a CSV file with columns: question,intent,answer
    # Then run: python src/train_from_csv.py
    
    csv_file = 'data/college_qa_dataset.csv'  # Your dataset path
    train_from_csv(csv_file)
