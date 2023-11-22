import time
import sqlalchemy as db
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import jwt
from flask import Flask
from flask import request,make_response

app=Flask(__name__)

engine=db.create_engine("sqlite:///empdatabase.sqlite")

conn=engine.connect()
metadata=db.MetaData()

Employee=db.Table("employee", metadata,
                     db.Column('id',db.Integer(),Primary_key=True),
                     db.Column('name',db.String(255)),
                     db.Column('address',db.String(255))
)

metadata.create_all(engine)
Base=declarative_base()
session=sessionmaker(bind=engine)()



class EmpInfo(Base):
    __tablename__="employee"
    id=Column(Integer,primary_key=True)
    name=Column(String)
    address=Column(String)
    
    def __init__(self,id,name,address):
        super().__init__()
        self.id=id
        self.name=name
        self.address=address
        
    def __str__(self):
        return str({'id':self.id,'name':self.name,'address':self.address})
    
    def validate(self):
        val_name=len(self.name)>0 and len(self.name)<256
        val_address=len(self.address)>0 and len(self.address)<256
        return val_name,val_address
class BaseException(Exception):
    status=400
    message=""
    def __init__(self,status,message)->None:
        super().__init__()
        self.status=status
        self.message=message
    def __str__(self):
        return str({'status':self.status,'message':self.message})
class ValidationError(BaseException):
    def __init__(self)->None:
        super().__init__(400,"Invalid Input Parameter")
class EmployeeNotPresentError(BaseException):
    def __init__(self, status, message) -> None:
        super().__init__(400, "Employee not present")

def setup_logger(called):
    def f(*args,**kwargs):
        request.logger=app.logger
        return called(*args,**kwargs)
    f.__name__=called.__name__
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
@app.route("/api/employee/",methods=["POST"])
@setup_logger
@time_request
@setup_tracing
def create_employee():
    user=request.json
    
    new_user=EmpInfo(id=user['id'],name=user['name'],address=user['address'])
    session.add(new_user)
    log_message = {'tracking_id': request.req_id,
                    'operation': 'create_employee',
                    'status': 'processing'}
    
    request.logger.info(str(log_message))
    session.commit()
   
    log_message['status'] = 'successful'
    request.logger.info(str(log_message))

    return str(new_user), 201

@app.route("/api/employee/<int:id>",methods=["GET"])
def get_employee_info(id):
    user = session.query(EmpInfo).get(id)
    if user:
        return str(user),200
    else :
        err=ValidationError(404,"Employee not present")
        return str(err),err.status
@app.route("/api/employee/<int:id>",methods=["PUT"])
@setup_logger
@time_request
@setup_tracing
def update_emp(id):
    detail=request.json
    change=session.query(EmpInfo).get(id)
    if change:
        change.id=detail.get('id',change.id)
        change.name = detail.get('name',change.name)
        change.address=detail.get('address',change.address)
        log_message = {'tracking_id': request.req_id,
                    'operation': 'update',
                    'status': 'processing'}
        request.logger.info(str(log_message))
    log_message['status'] = 'successful'
    request.logger.info(str(log_message))
    return str(change)

