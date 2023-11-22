import time
import sqlalchemy as db
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from flask import Flask, request, make_response
import jwt
from flask import jsonify



app = Flask(__name__)

engine = db.create_engine("sqlite:///empdatabase.sqlite")

conn = engine.connect()
metadata = db.MetaData()

Employee = db.Table("employee1", metadata,
                   db.Column('id', db.Integer(), primary_key=True),
                   db.Column('name', db.String(255)),
                   db.Column('address', db.String(255))
                   )

metadata.create_all(engine)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class EmpInfo(Base):
    __tablename__ = "employee1"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)

    def __init__(self, id, name, address):
        super().__init__()
        self.id = id
        self.name = name
        self.address = address

    def __str__(self):
        return str({'id': self.id, 'name': self.name, 'address': self.address})

    def validate(self):
        val_name = 0 < len(self.name) < 256
        val_address = 0 < len(self.address) < 256
        return val_name, val_address


class BaseException(Exception):
    status = 400
    message = ""

    def __init__(self, status, message):
        super().__init__()
        self.status = status
        self.message = message

    def __str__(self):
        return str({'status': self.status, 'message': self.message})


class ValidationError(BaseException):
    def __init__(self):
        super().__init__(400, "Invalid Input Parameter")


class EmployeeNotPresentError(BaseException):
    def __init__(self):
        super().__init__(400, "Employee not present")


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
@app.route("/api/authenticate",methods=['POST'])
def authenticate():
    
    data=request.json
    id=data['id']
    name_body=data['name']
    payload = {'sub': 'emp Token', 'emp_details': [id, name_body], 'iss': 'My Company',
'exp': 365 * 24 * 24 * 3600 * 24}
    details=session.query(EmpInfo).get(id)
    if details==None:
        return str({
            'status':400 , 'message':"invalid id"
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


def require_authentication(called):
    def f(*args,**kwargs):
        headers=request.headers
        token=headers['token']
        token_payload = jwt.decode(token, 'signing_key', algorithms= ['HS256'])
        #print(token_payload)
        #print(token_payload['emp_details'][0])
        a1=token_payload['emp_details'][0]
        data=request.json
        a2=data['id']
        #print(a2)
        if a1==a2:
            messg,resp=called(*args,**kwargs)
            #return called(*args, **kwargs)
            return messg,resp
        else:
            return str({
            'status':400 , 'message':"invalid id"
        }),400


    f.__name__ = called.__name__
    return f




@app.route("/api/employee/", methods=["POST"])
@setup_logger
@time_request
@setup_tracing
def create_employee():
    user = request.json

    new_user = EmpInfo(id=user['id'], name=user['name'], address=user['address'])
    session.add(new_user)
    log_message = {'tracking_id': request.req_id,
                   'operation': 'create_employee',
                   'status': 'processing'}

    request.logger.info(str(log_message))
    session.commit()

    log_message['status'] = 'successful'
    request.logger.info(str(log_message))

    return str(new_user), 201


@app.route("/api/employee/<int:id>", methods=["GET"])
def get_employee_info(id):
    user = session.query(EmpInfo).get(id)
    if user:
        return str(user), 200
    else:
        err = ValidationError()
        return str(err), err.status


@app.route("/api/employee/<int:id>", methods=["PUT"])
@require_authentication
@setup_logger
@time_request
@setup_tracing
def update_emp(id):
    detail = request.json
    change = session.query(EmpInfo).get(id)
    if change:
        change.id = detail.get('id', change.id)
        change.name = detail.get('name', change.name)
        change.address = detail.get('address', change.address)
        log_message = {'tracking_id': request.req_id,
                       'operation': 'update',
                       'status': 'processing'}
        request.logger.info(str(log_message))
        session.commit()
        log_message['status'] = 'successful'
        request.logger.info(str(log_message))
        #return str(change),200
        #return str({'message': 'Update successful', 'data': str(change)}), 200
        return jsonify({'message': 'Update successful', 'data': str(change)}), 200
    else:
        err = EmployeeNotPresentError()
        return str(err), err.status


if __name__ == "__main__":
    app.run(debug=True)
