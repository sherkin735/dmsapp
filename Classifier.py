__author__ = 'william'

import os
from sklearn.datasets import load_files
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.externals import joblib
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

CATEGORIES = os.listdir('./20news-bydate/20news-bydate-train')

class Classifier(object):

    def __init__(self, file_path):
        self.training_documents = load_files(container_path='./20news-bydate/20news-bydate-train',
                                       categories=CATEGORIES,
                                       decode_error='ignore',
                                       shuffle=True,
                                       encoding='utf-8',
                                       random_state=42)

        self.test_documents = load_files(container_path='./20news-bydate/20news-bydate-test',
                                       categories=CATEGORIES,
                                       decode_error='ignore',
                                       shuffle=True,
                                       encoding='utf-8',
                                       random_state=42)

        self.file_path = file_path


    def get_file_content(self):
        result=None
        extension = self.file_path.split('.')[-1]
        if extension == 'txt':
            with open(self.file_path, 'r') as myfile:
                result=myfile.read()
        elif extension == 'pdf':
            pass
            miner = pdf_converter()
            result = miner.convert_pdf_to_text(self.file_path)
        return result

    def classify_document(self):
        filename = './picklefiles/classifier.pkl'
        text_classifier = None
        try:
            text_classifier = joblib.load(filename)
        except IOError:
            if not text_classifier:
                print('Creating new model for classification')
                text_classifier = Pipeline([('vectorizer', CountVectorizer()),
                    ('tfidf', TfidfTransformer()),
                    ('classifier', MultinomialNB())
                ])
            text_classifier = text_classifier.fit(self.training_documents.data, self.training_documents.target)
            if not os.path.exists(filename):
                os.makedirs(os.path.dirname(filename))
            joblib.dump(text_classifier, filename)
            print('Model dumped to {0}'.format(filename))

        result = self.get_file_content()
        if result:
            predicted = text_classifier.predict([result])#self.test_documents.data)
            return self.training_documents.target_names[predicted]
        else:
            return "Unsupported File Type"
            #for document, category in zip("UnderstandingKernel", predicted):
                #print("{0} => {1}").format(document.split('/')[-1], self.training_documents.target_names[category])


class pdf_converter(object):

    def __init__(self):
        pass

    # http://stackoverflow.com/questions/26494211/extracting-text-from-a-pdf-file-using-pdfminer-in-python
    def convert_pdf_to_text(self, filepath):
        text = None
        try:
            rsrcmgr = PDFResourceManager()
            retstr = StringIO()
            codec = 'utf-8'
            laparams = LAParams()
            device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

            fp=file(filepath, 'rb')
            interpreter=PDFPageInterpreter(rsrcmgr, device)
            password=''
            maxpages=0
            caching=True
            pagenos=set()

            for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
                interpreter.process_page(page)

            text = retstr.getvalue()
            fp.close()
            device.close()
            retstr.close()
        except Exception, ex:
            print ex
            return False
        return text

if __name__ == '__main__':
    c = Classifier()
    c.classify_document()
    #miner = pdf_converter()
    #result = miner.convert_pdf_to_text()
    #print(result)
