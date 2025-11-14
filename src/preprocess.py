"""
Text preprocessing module for NLP chatbot
Cleans and tokenizes user input for ML model
"""

import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
    
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

# Keep important words that might be filtered as stop words
important_words = {'what', 'when', 'where', 'who', 'how', 'which', 'is', 'are', 'do', 'does', 'can', 'will', 'the'}
stop_words = stop_words - important_words


def clean_text(text):
    """
    Clean and normalize input text
    
    Args:
        text (str): Raw user input
        
    Returns:
        str: Cleaned text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Keep alphanumeric, spaces, and basic punctuation
    text = re.sub(r'[^a-z0-9\s\?\.]', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def tokenize(text):
    """
    Tokenize text into words
    
    Args:
        text (str): Input text
        
    Returns:
        list: List of tokens
    """
    return word_tokenize(text)


def remove_stopwords(tokens):
    """
    Remove stop words but keep important question words
    
    Args:
        tokens (list): List of word tokens
        
    Returns:
        list: Filtered tokens
    """
    return [word for word in tokens if word not in stop_words]


def lemmatize_tokens(tokens):
    """
    Lemmatize tokens to base form
    
    Args:
        tokens (list): List of word tokens
        
    Returns:
        list: Lemmatized tokens
    """
    return [lemmatizer.lemmatize(word) for word in tokens]


def preprocess(text):
    """
    Full preprocessing pipeline
    
    Args:
        text (str): Raw user input
        
    Returns:
        str: Preprocessed text ready for model
    """
    # Clean
    text = clean_text(text)
    
    # Tokenize
    tokens = tokenize(text)
    
    # Remove stopwords
    tokens = remove_stopwords(tokens)
    
    # Lemmatize
    tokens = lemmatize_tokens(tokens)
    
    # Join back to string
    return ' '.join(tokens)


def preprocess_patterns(patterns):
    """
    Preprocess a list of training patterns
    
    Args:
        patterns (list): List of text patterns
        
    Returns:
        list: List of preprocessed patterns
    """
    return [preprocess(pattern) for pattern in patterns]


if __name__ == '__main__':
    # Test the preprocessing
    test_sentences = [
        "What are the college timings?",
        "Tell me about Computer Science courses",
        "Who is the principal?",
        "How can I contact the admissions office?"
    ]
    
    print("Testing Preprocessing:\n")
    for sentence in test_sentences:
        processed = preprocess(sentence)
        print(f"Original: {sentence}")
        print(f"Processed: {processed}\n")
