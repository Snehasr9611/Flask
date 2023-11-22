import time
import sqlalchemy as db
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import jwt
from jwt import encode

from flask import Flask
from flask import request,make_response
app=Flask(__name__)

engine=db.create_engine("sqlite:///bank1.sqlite")

conn=engine.connect()
metadata=db.MetaData()

bankaccount=db.Table("account", metadata,
                     db.Column('acc_no',db.Integer()),
                     db.Column('name',db.String(255)),
                     db.Column('balance',db.Float()),
                     db.Column('aadhar_no',db.Integer()),
                     
)

metadata.create_all(engine)
Base=declarative_base()
session=sessionmaker(bind=engine)()



class BankAccount(Base):
    __tablename__="account"
    acc_no=Column(Integer,primary_key=True)
    name=Column(String)
    balance=Column(Float)
    aadhar_no=Column(Integer)
    
    
    def __init__(self,acc_no,name,balance,aadhar_no):
        super().__init__()
        self.acc_no=acc_no  
        self.name=name
        self.balance=balance
        self.aadhar_no=aadhar_no
    def __str__(self):
        # return f'{self.acc_no},{self.name},{self.balance},{self.aadhar_no}'
        return str({'acc_no':self.acc_no,'name':self.name,'balance':self.balance,'aadhar_no':self.aadhar_no})
class ValidationError(Exception):
    status = 400
    message = ""

    def __init__(self, status, message) -> None:
        super().__init__()
        self.status = status
        self.message = message

    def __str__(self):
        return str({'status': self.status, 'message': self.message})
def setup_logger(called):
    def f(*args, **kwargs):
        request.logger = app.logger
        return called(*args, **kwargs)
    f.__name__ = called.__name__
    return f

def time_request(called):
    def f(*args, **kwargs):
        request.start_time = time.time() * 1000
        res = called(*args, **kwargs)
        request.end_time = time.time() * 1000
        request.time = request.end_time - request.start_time
        app.logger.info('request time: {}'.format(request.time))
        return res
    f.__name__ = called.__name__
    return f

def setup_tracing(called):
    def f(*args, **kwargs):
        request.req_id = 'req_{}'.format(time.time() * 1000)
        res, status = called(*args, **kwargs)
        res_send = make_response(res)
        res_send.headers['X-Request-Id'] = request.req_id
        return res_send, status
    f.__name__ = called.__name__
    return f
def require_authentication(called):
    def f(*args,**kwargs):
        headers=request.headers
        token=headers['token']
        token_payload = jwt.decode(token, 'signing_key', algorithms= ['HS256'])
        #print(token_payload)
        #print(token_payload['acc_details'][0])
        a1=token_payload['acc_details'][0]
        data=request.json
        a2=data['acc_no']
        #print(a2)
        if a1==a2:
            return called(*args, **kwargs),200
        else:
            return str({
            'status':400 , 'message':"invalid acc_no"
        }),400


    f.__name__ = called.__name__
    return f
        
@app.route("/api/authenticate",methods=['POST'])
def authenticate():
    
    data=request.json
    acc_no=data['acc_no']
    name_body=data['name']
    payload = {'sub': 'bank Token', 'acc_details': [acc_no, name_body], 'iss': 'My Company',
'exp': 365 * 24 * 24 * 3600 * 24}
    details=session.query(BankAccount).get(acc_no)
    if details==None:
        return str({
            'status':400 , 'message':"invalid acc_no"
        }),400

    name=details.name
    if name==name_body:
        token = jwt.encode(payload, 'signing_key')
        return str({
            'token':token
        }),200
    else:
        return str({
            'status':400 , 'message':"invalid details"
        }),400




@app.route("/api/user/",methods=["POST"])
@setup_logger
@time_request
@setup_tracing
def create_user():
    user=request.json
    new_user=BankAccount(acc_no=user['acc_no'],name=user['name'],balance=user['balance'],aadhar_no=user['aadhar_no'])
    session.add(new_user)
    log_message = {'tracking_id': request.req_id,
                    'operation': 'create_user',
                    'status': 'processing'}
    
    request.logger.info(str(log_message))
    session.commit()
   
    log_message['status'] = 'successful'
    request.logger.info(str(log_message))

    return str(new_user), 201


@app.route("/api/user/<int:acc_no>",methods=["GET"])
def get_user_info(acc_no):
    user = session.query(BankAccount).get(acc_no)
    if user:
        return str(user),200
    else :
        err=ValidationError(404,"user not present")
        return str(err),err.status

@app.route("/api/user/<int:acc_no>",methods=["PUT"])
@setup_logger
@time_request
@setup_tracing
def transcation(acc_no):
    transaction_detail=request.json
    change=session.query(BankAccount).get(acc_no)
    if change:
        change.acc_no=transaction_detail.get('acc_no',change.acc_no)
        change.name = transaction_detail.get('name',change.name)
        change.aadhar_no=transaction_detail.get('aadhar_no',change.aadhar_no)
        log_message = {'tracking_id': request.req_id,
                    'operation': 'update',
                    'status': 'processing'}
        request.logger.info(str(log_message))
    log_message['status'] = 'successful'
    request.logger.info(str(log_message))
    return str(change)


@app.route("/api/update/<int:acc_no>",methods=['PUT'])
# @setup_logger
# @time_request
# @setup_tracing
@require_authentication
def transaction_update(acc_no):
    data = request.json
    print("here")
    user = session.query(BankAccount).get(acc_no)
    

    if data["type"] == "credit":
        user.balance += data["amount"]
    elif data["type"] == "debit":
        if data["amount"] > user.balance:
            return make_response('insufficient amount', 404)
        else:
            user.balance -= data["amount"]

    session.commit() 
    return str(user.balance)
 
# b1=BankAccount(1,'sss',1000,12345)
# print(session.add(b1))
# session.commit()
# import os
# from flask import Flask
from flask import request, send_file
# class BaseException(Exception):
#     status = 400
#     message = ""
#     def __init__(self, status, message) -> None:
#         super().__init__()
#         self.status = status
#         self.message = message
#     def __str__(self):
#         return str({'status': self.status, 'message': self.message})
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
