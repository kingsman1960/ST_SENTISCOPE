from flair.data import Sentence

class EntityExtractor:
    def __init__(self, flair_ner_model):
        self.flair_ner_model = flair_ner_model

    def extract_entities(self, text):
        """
        Extracting named entities using Flair and returning a dictionary with Flair entities.
        """
        entities = {}
        entities['Flair'] = self.extract_entities_flair(text)
        return entities

    def extract_entities_flair(self, text):
        sentence = Sentence(text)
        self.flair_ner_model.predict(sentence)
        entities = []
        for entity in sentence.get_spans('ner'):
            entities.append({'entity': entity.text, 'label': entity.tag})
        return entities
