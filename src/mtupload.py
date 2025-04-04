
import requests
import threading
import hashlib

test_file_hash = ""


def md5Checksum(filePath):
    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def hash_check(response_hash):
    if response_hash == test_file_hash:
        return "  HashOk"
    return "  HashError"


def upload():
    url = 'http://localhost:9802/post'
    files = {'file': ('test.pdf',
                      open('test.pdf', 'rb'),
                      'application/pdf',
                      {'Expires': '0'})}
    r = requests.post(url, files=files)
    print("StatusCode : " + str(r.status_code) +
          "  DocID : " + r.json()["id"] +
          hash_check(r.json()["hash"]) +
          "  ThreadName : "
          + threading.current_thread().name)


if __name__ == '__main__':
    try:
        test_file_hash = md5Checksum("test.pdf")

        tthreads = []
        for x in range(0, 50):
            thread = threading.Thread(target=upload)
            tthreads.append(thread)

        for t in tthreads:
            t.start()

        for t in tthreads:
            t.join()

    except Exception as errtxt:
        print(errtxt)
