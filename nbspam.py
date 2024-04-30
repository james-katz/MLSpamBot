'''
Script:
    nbspam.py
Description:
    Class for trainning and classifying messages as ham or spam.
Author:
    James Katz
Creation date:
    04/27/2024
Last modified date:
    04/27/2024
Version:
    1.0
'''

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from joblib import dump, load

class SpamClassifier:
    def __init__(self, csv_file):
        '''
            Initialize SpamClassifier class
            ### Parameters:
            - csv_file - The dataset in .csv format
        '''

        self.csv_file = csv_file
        self.messages = pd.read_csv(csv_file)
        self.vectorizer = None
        self.model = None
        self.load_models()

    def load_models(self):
        try:
            self.vectorizer = load('checkpoints/tfidf_checkpoint.joblib')
            self.model = load('checkpoints/model_checkpoint.joblib')
        except FileNotFoundError:
            self.train()

    def train(self):
        # Train-Test Split (Optional)        
        X_train, X_test, y_train, y_test = train_test_split(self.messages['message'].astype('str'), self.messages['spam'].astype('float'), test_size=0.2)

        # Vectorization using TfidfVectorizer
        self.vectorizer = TfidfVectorizer(
            lowercase=True
        )
        X_train_transformed  = self.vectorizer.fit_transform(X_train)
        X_test_transformed = self.vectorizer.transform(X_test)

        # Initialize and train the Model
        self.model = MultinomialNB()
        self.model.fit(X_train_transformed, y_train)

        # Make predictions on test data
        y_pred = self.model.predict(X_test_transformed)

        # Calculate accuracy
        accuracy = accuracy_score(y_test, y_pred)
        
        print("Model accuracy:", accuracy * 100)

        # Save the vectorizer and model objects as checkpoints
        dump(self.vectorizer, 'checkpoints/tfidf_checkpoint.joblib')
        dump(self.model, 'checkpoints/model_checkpoint.joblib')

    def add_entry(self, new_msg, is_spam):
        '''
            Add a new entry to the loaded dataset and re-train the model.
            ### Parameters:
            - new_msg: str -- The new message to add to the dataset.
            - is_spam:float -- Ham or spam (0.0 or 1.0)
        '''

        if new_msg is None or new_msg == '':
            return

        # New entry as a dict
        new_entry = {'message': [new_msg], 'spam': is_spam}
        # Convert new entry to a Pandas DataFrame
        new_entry_df = pd.DataFrame.from_dict(new_entry)

        # And concatenate the new entry with self.messages
        self.messages = pd.concat([self.messages, new_entry_df], ignore_index=True)

        # Save the new dataset to file        
        self.messages.to_csv(self.csv_file, index=False)
        
        # And re-train our model
        self.train()

    def get_accuracy(self):
        '''
            Get the model accuracy.
            ### Parameters:
            - None
            ### Returns:
            - float -- Accuracy of the model
        '''
         # Train-Test Split        
        _, X_test, _, y_test = train_test_split(self.messages['message'].astype('str'), self.messages['spam'].astype('float'), test_size=0.2)
        
        # Vectorization using TfidfVectorizer
        X_test_transformed = self.vectorizer.transform(X_test)

        # Make predictions on test data
        y_pred = self.model.predict(X_test_transformed)

        # Calculate accuracy
        accuracy = accuracy_score(y_test, y_pred)

        return accuracy * 100


    def predict(self, message):
        '''
            Predict if a message is ham or spam.
            ### Parameters:
            - message: str -- The message to evaluate.
            ### Returns:
            - float -- 0.0: Ham, 1.0: Spam
        '''

        message_transformed = self.vectorizer.transform([message])
        return self.model.predict(message_transformed)[0]