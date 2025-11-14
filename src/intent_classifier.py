"""
Intent Classification Module using Machine Learning
Trains and predicts user intent from preprocessed text
"""

import json
import pickle
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.preprocess import preprocess_patterns

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')


class IntentClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        self.model = LogisticRegression(max_iter=1000, random_state=42)
        self.intents = []
        self.intent_tags = []
        
    def load_intents(self, filepath=None):
        """Load intents from JSON file"""
        if filepath is None:
            filepath = os.path.join(DATA_DIR, 'intents.json')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.intents = data['intents']
        
        return self.intents
    
    def prepare_training_data(self):
        """Prepare training data from intents"""
        patterns = []
        labels = []
        self.intent_tags = []
        
        for intent in self.intents:
            tag = intent['tag']
            self.intent_tags.append(tag)
            
            for pattern in intent['patterns']:
                patterns.append(pattern)
                labels.append(tag)
        
        # Preprocess all patterns
        processed_patterns = preprocess_patterns(patterns)
        
        return processed_patterns, labels
    
    def train(self):
        """Train the intent classification model"""
        print("Loading intents...")
        self.load_intents()
        
        print("Preparing training data...")
        X, y = self.prepare_training_data()
        
        print(f"Total training samples: {len(X)}")
        print(f"Number of intent classes: {len(set(y))}")
        
        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print("\nVectorizing text...")
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        print("Training model...")
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✓ Training complete!")
        print(f"Accuracy: {accuracy * 100:.2f}%\n")
        print("Classification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model
        self.save_model()
        
        return accuracy
    
    def save_model(self):
        """Save trained model and vectorizer"""
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        model_path = os.path.join(MODEL_DIR, 'intent_model.pkl')
        vectorizer_path = os.path.join(MODEL_DIR, 'vectorizer.pkl')
        tags_path = os.path.join(MODEL_DIR, 'intent_tags.pkl')
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        with open(tags_path, 'wb') as f:
            pickle.dump(self.intent_tags, f)
        
        print(f"✓ Model saved to {MODEL_DIR}/")
    
    def load_model(self):
        """Load trained model from disk"""
        model_path = os.path.join(MODEL_DIR, 'intent_model.pkl')
        vectorizer_path = os.path.join(MODEL_DIR, 'vectorizer.pkl')
        tags_path = os.path.join(MODEL_DIR, 'intent_tags.pkl')
        
        if not os.path.exists(model_path):
            raise FileNotFoundError("Model not found. Please train the model first.")
        
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        with open(tags_path, 'rb') as f:
            self.intent_tags = pickle.load(f)
        
        # Load intents for responses
        self.load_intents()
    
    def predict(self, text):
        """
        Predict intent from user input
        
        Args:
            text (str): User input text
            
        Returns:
            dict: Predicted intent info with tag and confidence
        """
        # Preprocess
        from src.preprocess import preprocess
        processed = preprocess(text)
        
        # Vectorize
        X = self.vectorizer.transform([processed])
        
        # Predict
        intent_tag = self.model.predict(X)[0]
        confidence = np.max(self.model.predict_proba(X))
        
        # Get intent details
        intent_data = None
        for intent in self.intents:
            if intent['tag'] == intent_tag:
                intent_data = intent
                break
        
        return {
            'tag': intent_tag,
            'confidence': confidence,
            'intent_data': intent_data
        }


def train_model():
    """Train and save the intent classification model"""
    classifier = IntentClassifier()
    classifier.train()


if __name__ == '__main__':
    # Train the model
    print("=" * 60)
    print("INTENT CLASSIFIER TRAINING")
    print("=" * 60 + "\n")
    
    train_model()
    
    print("\n" + "=" * 60)
    print("Testing predictions...")
    print("=" * 60 + "\n")
    
    # Test predictions
    classifier = IntentClassifier()
    classifier.load_model()
    
    test_queries = [
        "What are the college timings?",
        "Tell me about courses",
        "Who is the principal?",
        "How can I apply for admission?",
        "What facilities do you have?"
    ]
    
    for query in test_queries:
        result = classifier.predict(query)
        print(f"Query: {query}")
        print(f"Intent: {result['tag']} (confidence: {result['confidence']:.2f})")
        print()
