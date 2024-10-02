import nltk
from flair.data import Sentence
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

class EntityExtractor:
    def __init__(self, flair_ner_model):
        self.flair_ner_model = flair_ner_model
        # Ensure NLTK data is downloaded
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('maxent_ne_chunker')
        nltk.download('words')
        
        # Initialize SEC-BERT-BASE
        self.sec_bert_tokenizer = AutoTokenizer.from_pretrained("nlpaueb/sec-bert-base")
        self.sec_bert_model = AutoModelForTokenClassification.from_pretrained("nlpaueb/sec-bert-base")
        self.sec_bert_nlp = pipeline("ner", model=self.sec_bert_model, tokenizer=self.sec_bert_tokenizer, aggregation_strategy="simple")

    def extract_entities(self, text):
        """
        Extracting named entities using Flair, NLTK, and SEC-BERT-BASE and returning a dictionary with entities.
        """
        entities = {}
        entities['Flair'] = self.extract_entities_flair(text)
        entities['NLTK'] = self.extract_entities_nltk(text)
        entities['SEC-BERT'] = self.extract_entities_sec_bert(text)
        return entities

    def extract_entities_flair(self, text):
        sentence = Sentence(text)
        self.flair_ner_model.predict(sentence)
        entities = []
        for entity in sentence.get_spans('ner'):
            entities.append({'entity': entity.text, 'label': entity.tag})
        return entities

    def extract_entities_nltk(self, text):
        tokens = nltk.word_tokenize(text)
        pos_tags = nltk.pos_tag(tokens)
        tree = nltk.ne_chunk(pos_tags)
        entities = []
        for subtree in tree:
            if isinstance(subtree, nltk.Tree):
                entity_text = ' '.join([word for word, tag in subtree.leaves()])
                entity_label = subtree.label()
                entities.append({'entity': entity_text, 'label': entity_label})
        return entities

    def extract_entities_sec_bert(self, text):
        ner_results = self.sec_bert_nlp(text)
        entities = []
    
        # Define a mapping for SEC-BERT entity labels
        label_mapping = {
            'ORG': 'Organization',
            'PER': 'Person',
            'LOC': 'Location',
            'MISC': 'Miscellaneous',
            'GPE': 'Geopolitical Entity',
            'DATE': 'Date',
            'MONEY': 'Money',
            'PERCENT': 'Percentage',
            'TIME': 'Time',
            'CARDINAL': 'Cardinal Number',
            'ORDINAL': 'Ordinal Number',
            'QUANTITY': 'Quantity',
            'PRODUCT': 'Product',
            'EVENT': 'Event',
            'NORP': 'Nationality or Religious or Political Group',
            'FAC': 'Facility',
            'WORK_OF_ART': 'Work of Art',
            'LAW': 'Law',
            'LANGUAGE': 'Language'
        }

        for entity in ner_results:
        # Map the entity label to a more descriptive one, or keep the original if not in the mapping
            mapped_label = label_mapping.get(entity['entity_group'], entity['entity_group'])
            entities.append({
                'entity': entity['word'],
                'label': mapped_label
            })
    
            return entities
