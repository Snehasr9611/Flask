import os
from flask import Flask
from flask import request, send_file
class BaseException(Exception):
    status = 400
    message = ""
    def __init__(self, status, message) -> None:
        super().__init__()
        self.status = status
        self.message = message
    def __str__(self):
        return str({'status': self.status, 'message': self.message})
class FileExistsException(BaseException):
    def __init__(self) -> None:
        super().__init__(400, "File with id already exists")
class FileDoesNotExistsException(BaseException):
    def __init__(self) -> None:
        super().__init__(400, "File with id does not exist")
app = Flask(__name__)
@app.route('/api/files/', methods=['POST'])
def create_file():
    log_message = {
        'operation': 'create file',
        'status': 'processing'
                }
    app.logger.info(str(log_message))
# Access the text part of the mulipart request.
    data = dict(request.form)
    file_name = data.get('name')
    file_id = data.get('file_id')
    file_path = os.getcwd() + '/storage/'
    print(file_path)
# Access the file object
    file = request.files['file']
    overwrite = data.get('overwrite', False)
    if not overwrite and os.path.isfile(file_id):
        log_message['status'] = 'unsuccessful'
        log_message['reason'] = 'File Already exists'
        app.logger.error(str(log_message))
        err = exceptions.FileExistsException()
        return str(err), err.status
    else:
        log_message['status'] = 'successful'
        app.logger.info(str(log_message))
        file.save(file_path + file_id)
        return "", 200
@app.route('/api/files/<file_id>', methods=['GET'])
def get_file(file_id):
    log_message = {
        'operation': 'get file',
        'status': 'processing'
                }
    app.logger.info(str(log_message))

    file_path = os.getcwd() + '\storage\\{}'.format(file_id)
# Check if the file exists.
    if not os.path.isfile(file_path):
        log_message['status'] = 'unsuccessful'
        log_message['reason'] = 'File Does not exist'
        app.logger.error(str(log_message))
        err = exceptions.FileDoesNotExistsException()
        return str(err), err.status
    else:
        log_message['status'] = 'successful'
        app.logger.info(log_message)
        return send_file(file_path), 200
@app.route('/api/files/<file_id>', methods=['DELETE'])
def remove_file(file_id):
    log_message = {
        'operation': 'remove file',
        'status': 'processing'
                }   
    app.logger.info(str(log_message))
    file_path = os.getcwd() + '\storage\\{}'.format(file_id)
# Check if the file exists.
    if not os.path.isfile(file_path):
        log_message['status'] = 'unsuccessful'
        log_message['reason'] = 'File Does not exist'
        app.logger.error(str(log_message))
        err = exceptions.FileDoesNotExistsException()
        return str(err), err.status
    else:
# Delete the file.
        os.remove(file_path)
        log_message['status'] = 'successful'
        app.logger.info(log_message)
        return "", 200