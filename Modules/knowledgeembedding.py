import pandas as pd
from knowledgebase import KB, extract_triples
import pykeen
from pykeen.triples import TriplesFactory

class KGE():
    """
    generate triples suitable for PyKeen from knowledge base class object.
    if specified does a [train test] or [train test validate split]
    """
    def __init__(self, data):
        self.data = []
        
    def kb2tf(kb, split = []):
        """
        returns TripleFactory type triples,
        split = given array specifying train,test,val distribution
        returns Triple factory type triples for train, test, val set.
        if specified does a [train test] or [train test validate split]
        """
        df = pd.DataFrame([r.values() for r in kb.relations], columns = ['head', 'type', 'tail'])
        tf = TriplesFactory.from_labeled_triples(df[['head', 'type', 'tail']].values, create_inverse_triples = True)
        if len(split)==2:
            train, test = tf.split(split)
            return df, tf, train, test

        elif len(split) == 3:
            train, test, val = tf.split(split)
            return df, tf, train, test, val



