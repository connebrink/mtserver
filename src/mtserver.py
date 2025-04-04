
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

import threading
import os
import json
import uuid
import cgi
import hashlib

DOC_STORAGE_PATH = "~/Projects/storage/"


class Handler(BaseHTTPRequestHandler):
    def _check_doc_tree(self):
        if not os.path.isdir(DOC_STORAGE_PATH):
            os.mkdir(DOC_STORAGE_PATH)

    def _exists_document(self, docid):
        self._check_doc_tree()
        docpath = DOC_STORAGE_PATH + docid
        return os.path.exists(docpath)

    def _create_document_store_item(self, new_doc_id, new_doc_blob_path, new_doc_desc_path):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST',
                     'CONTENT_TYPE': self.headers['Content-Type'],
                     })
        filename = form['file'].filename
        data = form['file'].file.read()

        open(new_doc_blob_path, "wb").write(data)

        hash_object = hashlib.md5(data)

        result_json_data = {
            "id": str(new_doc_id),
            "filename": filename,
            "length":  str(len(data)),
            "type": self.headers['Content-Type'],
            "hash": hash_object.hexdigest()
        }

        result_json = json.dumps(result_json_data)

        open(new_doc_desc_path, "wb").write(str.encode(result_json))

        return result_json

    def _create_document(self):
        self._check_doc_tree()

        new_doc_id = uuid.uuid4()

        new_doc_root_path = DOC_STORAGE_PATH + str(new_doc_id) + "/"
        new_doc_blob_path = new_doc_root_path + str(new_doc_id) + ".blob"
        new_doc_desc_path = new_doc_root_path + str(new_doc_id) + ".desc"

        os.mkdir(new_doc_root_path)

        result_json = self._create_document_store_item(new_doc_id=new_doc_id,
                                                       new_doc_blob_path=new_doc_blob_path,
                                                       new_doc_desc_path=new_doc_desc_path)

        self.send_response(201)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(result_json)))
        self.end_headers()

        self.wfile.write(str.encode(result_json))

    def _send_invalid_request_reponse(self):
        self.send_error(401)
        self.end_headers()
        return

    def _send_not_found_response(self):
        self.send_error(404)
        self.end_headers()
        return

    def _read_document_description(self, document_description_file):
        description = ""
        try:
            with open(document_description_file) as json_data:
                description = json.load(json_data)
                json_data.close()
        except Exception as e:
            ee = e.message
            print(ee)

        return description

    def _send_document_data(self, docid):
        doc_blob_file_path = DOC_STORAGE_PATH + '/' + docid + '/' + docid + ".blob"
        doc_desc_file_path = DOC_STORAGE_PATH + '/' + docid + '/' + docid + ".desc"

        document_description = self._read_document_description(doc_desc_file_path)
        document_file = open(doc_blob_file_path, 'rb')

        self.send_response(200)
        # self.send_header("Content-type", str(document_description["type"]))
        self.send_header("Content-type", "application/pdf")
        self.send_header("Content-Length", str(document_description["length"]))
        self.end_headers()

        while True:
            file_data = document_file.read(32768)
            if file_data is None or len(file_data) == 0:
                break
            self.wfile.write(file_data)

        document_file.close()

    def do_GET(self):
        """Download document binary data"""
        print("CurrentThread  : " + threading.current_thread().getName())
        query = urlparse(self.path).query
        if query is None or len(query) == 0:
            self._send_invalid_request_reponse()
            return

        query_components = dict(qc.split("=") for qc in query.split("&"))
        if query_components is None or len(query_components) == 0:
            self._send_invalid_request_reponse()
            return

        docid = query_components["docid"]
        if docid is None or len(docid) == 0:
            self._send_invalid_request_reponse()
            return

        if not self._exists_document(docid=docid):
            self._send_not_found_response()
            return

        self._send_document_data(docid)

        return

    def do_POST(self):
        """Upload document binary data"""
        print("")
        self._create_document()

        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Erts sample of nonblocking multithread server for uploads and downloads"""


if __name__ == '__main__':
    server = ThreadedHTTPServer(('localhost', 9802), Handler)
    print(':: MTUDServer at localhost:9802')
    print(':: Erts sample of nonblocking multithread server for uploads and downloads')
    print(':: Starting server, use any key to stop')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
