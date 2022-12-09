from fuzzywuzzy import fuzz
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, BertTokenizer
import pandas as pd
import math
import torch
import json

class KB():
    """
    Knowledge Base Class to convert tabular data into 
    an array (relations) of triple dictionaries {head = , type = , tail =}
    also stores unique entities in a dictionary (entities)
    """
    def __init__(self):
        self.relations = []
        self.entities = {}
    
    def add_entity(self, e):
        """
        stores unique entities
        """
        self.entities[e] = []
        

    def are_relations_equal(self, r1, r2):
        """
        check for duplicate relations before adding them to the array
        input:
        r1, r2 -- triples to be compared
        fuzzy matches the strings that belong to each triple attribute
        output: 

        """
        return all(self.fuzzy_equal(r1[attr], r2[attr]) for attr in ["head", "tail"])
    
    def exists_relation(self, r1):
        """
        iterates through the existing kb to see if the input triple 
        matches any existing relations
        input:
        r1 -- triple to be compared
        output:
        returns true if there is any fuzzymatch between a relation and input
        """
        return any(self.are_relations_equal(r1, r2) for r2 in self.relations)
    
    #we also need to check if the relation contains a company name, or is a triplet
    #relating to the company, in which case the triplet is related to the company
    #via the description link
    
    #function that checks loosely checks for equality btw strings
    def fuzzy_equal(self, str1, str2):
        ratio1 = fuzz.partial_ratio(str1.lower(), str2.lower())
        ratio2 = fuzz.partial_ratio(str1.lower(), str2.lower())
        return (ratio1 > 95) or (ratio2 > 95)

    #add relation to knowledge base if it doesn't exist, if company name is not in the triple
    # add company name triple pointing to the current triple
    def add_relation(self, r):
        if not self.exists_relation(r):
            if not self.fuzzy_equal(r['head'], r['tail']):
                self.relations.append(r)
                 
                entities = [r["head"], r["tail"]]

                for ent in entities:
                    self.add_entity(ent)

                if 'meta' in r:
                    if self.fuzzy_equal(r["head"], r['meta']['comp']) != self.fuzzy_equal(r["tail"], r['meta']['comp']):
                        if self.fuzzy_equal(r["head"], r['meta']['comp']):
                            r["head"] = r['meta']['comp']
                        else:
                            r2 = {
                            'head': r['meta']['comp'],
                            'type': "description",
                            'tail': r["head"], }
                            r2['meta'] = {
                                "comp": r['meta']['comp']}
                            self.add_relation(r2)

                        if self.fuzzy_equal(r["tail"], r['meta']['comp']):
                            r["tail"] = r['meta']['comp']    
            else:
                return
            
    def merge_with_kb(self, kb2):
        """
        merges two kbs by joining relations
        """
        for r in kb2.relations:
            self.add_relation(r)

    def print(self):
        """
        prints relations
        """
        print("Relations:")
        for r in self.relations:
            print(f"  {r}")
    

            
class extract_triples:
    """
    class for generating triplets given a variety of datasets
    """

    def comp(df, relations = [], v_list = [], name ="org_name" ):
        """
        generates triplets linking the organisation name to the attributes stored in the columns
        name = the name of columnn that stores the company name
        v_list = contains all columns that contain an attribute list.
        """
        for i in range(df.shape[1]):
            col = df.columns[i]
            if (col != name):
                for n, ele in enumerate(df[col]):
                        if col in v_list:
                            for item in ele.split(','):
                                relations.append({
                                'head': df[name][n],
                                'type': col,
                                'tail': str(item)
                            })   

                        else: 
                            relations.append({
                            'head': df['org_name'][n],
                            'type': col,
                            'tail': str(ele)
                            })
        kb = KB()
        for i, relation in enumerate(relations):
            if i%100 == 0:
                print(f"Completed {i/len(relations)*100} %")
            kb.add_relation(relation)
        return kb

    def founder(df, relations = []):
        """
        generates triplets linking the founder name to the attributes stored in the columns
        """
        name = ['founder_name']
        for i in range(df.shape[1]):
            col = df.columns[i]
            if (col not in name):
                for n, ele in enumerate(df[col]):
                        for item in ele.split(','):
                            relations.append({
                            'head': df['founder_name'][n],
                            'type': col,
                            'tail': str(item) })
        kb = KB()
        for i, relation in enumerate(relations):
            if i%100 == 0:
                print(f"Completed {i/len(relations)*100} %")
            kb.add_relation(relation)
        return kb
    #creates triplet for the investor similar to comp, probably can be one function
    
    def inv(df, relations = [], v_list = []):
        """
        generates triplets linking the investor name to the attributes stored in the columns
        """
        name = ['investor_name', "investor_uuid"]
        for i in range(df.shape[1]):
            col = df.columns[i]
            if (col not in name):
                for n, ele in enumerate(df[col]):
                        if col in v_list:
                            for item in ele.split(','):
                                relations.append({
                                'head': df['investor_name'][n],
                                'type': col,
                                'tail': str(item)
                            })

                        else: 
                            relations.append({
                            'head': df['investor_name'][n],
                            'type': col,
                            'tail': str(ele)
                            })   
        kb = KB()
        for i, relation in enumerate(relations):
            if i%100 == 0:
                print(f"Completed {i/len(relations)*100} %")
            kb.add_relation(relation)
        return kb
    

    def from_desc_to_kb(df, verbose=False):
        """
        converts all company descriptions into a kb
        returns the kb
        """
        def extract_relations_from_model_output(text):
            """
            model function from REBEL
            https://huggingface.co/Babelscape/rebel-large

            text = description to be processed
            returns triples from input description
            """
            relations = []
            relation, subject, relation, object_ = '', '', '', ''
            text = text.strip()
            current = 'x'
            text_replaced = text.replace("<s>", "").replace("<pad>", "").replace("</s>", "")
            for token in text_replaced.split():
                if token == "<triplet>":
                    current = 't'
                    if relation != '':
                        relations.append({
                            'head': subject.strip(),
                            'type': relation.strip(),
                            'tail': object_.strip()
                        })
                        relation = ''
                    subject = ''
                elif token == "<subj>":
                    current = 's'
                    if relation != '':
                        relations.append({
                            'head': subject.strip(),
                            'type': relation.strip(),
                            'tail': object_.strip()
                        })
                    object_ = ''
                elif token == "<obj>":
                    current = 'o'
                    relation = ''
                else:
                    if current == 't':
                        subject += ' ' + token
                    elif current == 's':
                        object_ += ' ' + token
                    elif current == 'o':
                        relation += ' ' + token
            if subject != '' and relation != '' and object_ != '':
                relations.append({
                    'head': subject.strip(),
                    'type': relation.strip(),
                    'tail': object_.strip()
                })
            return relations
        
        def from_row_to_kb(df, span_length=128, verbose=False):
        
            """
            model function from REBEL
            https://huggingface.co/Babelscape/rebel-large

            df = dataframe that contains the description texts.
            returns knowledge base for one description
            """

            tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
            #tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")
            comp = df['org_name']
            text = df['long_description']
            # tokenize whole text
            inputs = tokenizer([text], return_tensors="pt")
            # compute span boundaries
            num_tokens = len(inputs["input_ids"][0])
            if verbose:
                print(f"Input has {num_tokens} tokens")
            num_spans = math.ceil(num_tokens / span_length)
            if verbose and num_tokens > 1:
                print(f"Input has {num_spans} spans")
            overlap = math.ceil((num_spans * span_length - num_tokens) / 
                                max(num_spans - 1, 1))
            spans_boundaries = []
            start = 0
            for i in range(num_spans):
                spans_boundaries.append([start + span_length * i,
                                         start + span_length * (i + 1)])
                start -= overlap
            #if verbose:
                #print(f"Span boundaries are {spans_boundaries}")

            # transform input with spans
            tensor_ids = [inputs["input_ids"][0][boundary[0]:boundary[1]]
                          for boundary in spans_boundaries]
            tensor_masks = [inputs["attention_mask"][0][boundary[0]:boundary[1]]
                            for boundary in spans_boundaries]
            inputs = {
                "input_ids": torch.stack(tensor_ids),
                "attention_mask": torch.stack(tensor_masks)
            }

            # generate relations
            num_return_sequences = 3
            gen_kwargs = {
                "max_length": 256,
                "length_penalty": 0,
                "num_beams": 3,
                "num_return_sequences": num_return_sequences
            }
            generated_tokens = model.generate(
                **inputs,
                **gen_kwargs,
            )

            # decode relations
            decoded_preds = tokenizer.batch_decode(generated_tokens,
                                                   skip_special_tokens=False)

            # create kb
            kb = KB()
            i = 0
            for sentence_pred in decoded_preds:
                current_span_index = i // num_return_sequences
                relations = extract_relations_from_model_output(sentence_pred)
                for relation in relations:
                    relation["meta"] = {
                        "comp": comp
                    }
                    kb.add_relation(relation)
                i += 1
            return kb
    
        #iterate through descriptions, create kb for each description and join.
        kb = KB()
        if verbose:
            print(f"{len(df)} links to visit")
        for i in range(len(df)):
            if verbose:
                print(f"Visiting {descriptions['name'][i]}...")
            kb_comp = from_row_to_kb(df.iloc[i], verbose=verbose)
            kb.merge_with_kb(kb_comp)
            if i%100 == 0:
                print('On row {i}')
        return kb

    def founder_data(df_link, df_comp):
        """
        extracts relevant founder data from json
        """
        weave_founder_s = pd.DataFrame(columns = ['org_uuid','founder_name','founder_school','founder_degree', 'founder_exp', 'founder_roles'])
        for i, row in df_link.iterrows():
            temp = []
            try:
                pjs = json.loads(row['json_string'])
            except:
                pass
            school = []
            employer = []
            degree = []
            role = []

            try:
                name = pjs['data'][0]['allNames'][0]
            except:
                name = ''
            try:
                for education in pjs['data'][0]['educations']:
                    if 'degree' in education:
                        school.append(education['institution']['name'])
                        degree.append(education['degree']['name'])

                    else:
                        school.append(education['institution']['name'])
                        degree.append('')
            except:
                school.append('')
                degree.append('')

            try:
                for employment in pjs['data'][0]['employments']:
                    try:
                        employer.append(employment['employer']['name'])
                    except:
                        employer.append('')
                    if 'title' in employment:
                        role.append(employment['title'])
                    else:
                        role.append('')
            except:
                employer.append('')
                role.append('')

            temp.append(row['org_uuid'])
            temp.append(name)
            temp.append(','.join(school))
            temp.append(','.join(degree))
            temp.append(','.join(employer))
            temp.append(','.join(role))

            df_temp = pd.DataFrame([temp], columns = weave_founder_s.columns)
            weave_founder_s = pd.concat([weave_founder_s,df_temp], ignore_index = True)

        df_founder_s = df_comp[['org_uuid', 'org_name']].merge(weave_founder_s, on = 'org_uuid').reset_index(drop = True).drop(columns = 'org_uuid')
        df_founder_s = df_founder_s.drop_duplicates(subset = 'founder_name').reset_index(drop = True)
        return df_founder_s
