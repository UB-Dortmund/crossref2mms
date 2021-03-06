# The MIT License
#
#  Copyright 2016-2017 UB Dortmund <daten.ub@tu-dortmund.de>.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import datetime
import requests
from simplejson import JSONDecodeError
import uuid

# https://github.com/CrossRef/rest-api-doc/blob/master/rest_api.md

CROSSREF_API_URL = 'http://api.crossref.org/works/%s'

CROSSREF_PUBTYPES = {
    'book': 'Monograph',
    'book-chapter': 'Chapter',
    'book-edited': 'Collection',
    'book-section': 'Chapter',
    'book-series': 'Series',
    'book-set': 'Monograph',
    'book-track': 'Chapter',
    'component': 'Report',
    'data-set': 'ResearchData',
    'dissertation': 'Thesis',
    'journal-article': 'ArticleJournal',
    'journal': 'Journal',
    'journal-issue': 'Collection',
    'journal-volume': 'Collection',
    'monograph': 'Monograph',
    'other': 'Report',
    'preprint': 'Report',
    'proceedings': 'Conference',
    'proceedings-article': 'Chapter',
    'reference': 'Collection',
    'reference-entry': 'Chapter',
    'report': 'Report',
    'report-series': 'Series',
    'standard': 'Standard',
    'standard-series': 'Series',
}


def crossref2mms(doi=''):

    mms_json = {}

    record = {}
    try:
        record = requests.get(CROSSREF_API_URL % doi).json()
    except JSONDecodeError:
        pass

    try:
        if record.get('message'):
            mms_json.setdefault('id', str(uuid.uuid4()))
            timestamp = str(datetime.datetime.now())
            mms_json.setdefault('created', timestamp)
            mms_json.setdefault('changed', timestamp)
            mms_json.setdefault('editorial_status', 'new')

            pubtype = CROSSREF_PUBTYPES.get(record.get('message').get('type'))
            mms_json.setdefault('pubtype', pubtype)

            title = record.get('message').get('title')[0]
            mms_json.setdefault('title', title)

            issued = record.get('message').get('created').get('date-parts')[0][0]
            if record.get('message').get('created').get('date-parts')[0][1]:
                issued = '%s-%s' % (issued, record.get('message').get('created').get('date-parts')[0][1])
            if record.get('message').get('created').get('date-parts')[0][2]:
                issued = '%s-%s' % (issued, record.get('message').get('created').get('date-parts')[0][2])

            mms_json.setdefault('issued', issued)

            is_part_of = []
            if record.get('message').get('container-title'):
                for jtitle in record.get('message').get('container-title'):
                    if jtitle != '':
                        part = {}
                        part.setdefault('is_part_of', jtitle)
                        if record.get('message').get('volume'):
                            part.setdefault('volume', record.get('message').get('volume'))
                        if record.get('message').get('issue'):
                            part.setdefault('issue', record.get('message').get('issue'))
                        if record.get('message').get('page_first'):
                            part.setdefault('page_first', record.get('message').get('page_first'))
                        if record.get('message').get('page_last'):
                            part.setdefault('page_last', record.get('message').get('page_last'))
                        if record.get('message').get('page'):
                            page = str(record.get('message').get('page')).split('-')
                            part.setdefault('page_first', page[0])
                            if len(page) > 1:
                                part.setdefault('page_last',  page[1])
                        is_part_of.append(part)
                        break

            if record.get('message').get('parent-title'):
                for jtitle in record.get('message').get('parent-title'):
                    if jtitle != '':
                        part = {}
                        part.setdefault('is_part_of', jtitle)
                        if record.get('message').get('volume'):
                            part.setdefault('volume', record.get('message').get('volume'))
                        if record.get('message').get('issue'):
                            part.setdefault('issue', record.get('message').get('issue'))
                        if record.get('message').get('page_first'):
                            part.setdefault('page_first', record.get('message').get('page_first'))
                        if record.get('message').get('page_last'):
                            part.setdefault('page_last', record.get('message').get('page_last'))
                        if record.get('message').get('page'):
                            page = str(record.get('message').get('page')).split('-')
                            part.setdefault('page_first', page[0])
                            if len(page) > 1:
                                part.setdefault('page_last',  page[1])
                        is_part_of.append(part)
                        break

            if len(is_part_of) > 0:
                mms_json.setdefault('is_part_of', is_part_of)

            persons = []
            if record.get('message').get('author'):
                for author in record.get('message').get('author'):
                    person = {}
                    person.setdefault('name', '%s, %s' % (author.get('family'), author.get('given')))
                    person.setdefault('role', []).append('aut')
                    persons.append(person)

            if record.get('message').get('editor'):
                for editor in record.get('message').get('editor'):
                    person = {}
                    person.setdefault('name', '%s, %s' % (editor.get('family'), editor.get('given')))
                    person.setdefault('role', []).append('edt')
                    persons.append(person)

            if len(persons) > 0:
                mms_json.setdefault('person', persons)

            publisher = record.get('message').get('publisher')
            mms_json.setdefault('publisher', publisher)

            mms_json.setdefault('DOI', []).append(doi)

            if record.get('message').get('ISBN'):
                isbns = []
                for isbn in record.get('message').get('ISBN'):
                    if 'isbn/' in isbn.strip():
                        isbns.append(isbn.strip().split('isbn/')[1])
                    else:
                        isbns.append(isbn.strip())
                mms_json.setdefault('isbn', isbns)

    except:
        mms_json = {}

    return mms_json

if __name__ == '__main__':

    # TODO tests
    print('Tests are coming soon!')
