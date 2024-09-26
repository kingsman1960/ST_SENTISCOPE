import nltk
from flair.data import Sentence

class EntityExtractor:
    def __init__(self, flair_ner_model):
        self.flair_ner_model = flair_ner_model
        # Ensure NLTK data is downloaded
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('maxent_ne_chunker')
        nltk.download('words')

    def extract_entities(self, text):
        """
        Extracting named entities using both Flair and NLTK and returning a dictionary with entities.
        """
        entities = {}
        entities['Flair'] = self.extract_entities_flair(text)
        entities['NLTK'] = self.extract_entities_nltk(text)
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
