from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class Note(db.Model):                                                 #공지사항 또는 업무소통
    id = db.Column(db.Integer, primary_key=True)                      #DB primary_key ID
    data = db.Column(db.String(1000))                                 #공지글
    noteuname = db.Column(db.String(20))                              #작성자 이름
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):                                      #Employee
    id = db.Column(db.Integer, primary_key=True)                      #DB primary_key ID
    email = db.Column(db.String(50), unique=True)                     #이름대신 ID로 사용함
    uname = db.Column(db.String(50),nullable=False)                   #이름
    udepartment = db.Column(db.String(50))                            #소속부서
    uposition = db.Column(db.String(50))                              #직책
    password = db.Column(db.String(50))                               #패스워드
    authority = db.Column(db.String(10))                              #권한관리 : 1 슈퍼 관리자, 2 관리자, 3 일반 사용자
    notes = db.relationship('Note')                                   #외래키 연동
    projects = db.relationship('Project')
    working_hours = db.relationship('Working_hour')
 
class Project(db.Model):                                              #새 프로젝트를 생성한다.(관리자) 1번
    pid = db.Column(db.Integer, primary_key=True)                     #DB primary_key ID
    pcode = db.Column(db.String(50), unique=True, nullable=False)     #프로젝트 코드
    pname = db.Column(db.String(100), nullable=False)                 #프로젝트 이름
    startdate = db.Column(db.String(50))                              #시작일자
    enddate = db.Column(db.String(50))                                #종료일자
    pdesc = db.Column(db.String(100))                                 #프로젝트 설명 
    date = db.Column(db.DateTime(timezone=True), default=func.now())  #등록일자 timestamp
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))         #외래키 연동

class Working_hour(db.Model):                                         #내가 참여중인 프로젝트에 MD를 매일 등록한다. 
    id = db.Column(db.Integer, primary_key=True)                      #DB primary_key ID
    pcode = db.Column(db.String(50), nullable=False)                  #프로젝트 코드
    pname = db.Column(db.String(100))                                 #프로젝트 이름
    username = db.Column(db.String(50))                               #사용자 이름
    jobpart = db.Column(db.String(50))                                #업무 진행한 분야(근무시간을 쓴 곳)
    workhour = db.Column(db.Integer)                                  #프로젝트에 사용한 시간을 입력
    recodingdate = db.Column(db.String(50))                           #근무기록한 날짜 'yymmdd'
    date = db.Column(db.DateTime(timezone=True), default=func.now())  #timestamp
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))         #외래키 연동

class Cocompany(db.Model):   #User과 같은 역할로 외주업체 MD 등록
    id = db.Column(db.Integer, primary_key=True)
    saname = db.Column(db.String(50),unique=True, nullable=False)      #회사명
    sourcingjob = db.Column(db.String(50))                             #외주업무
    saboss = db.Column(db.String(50))                                  #대표자명
    saaddr = db.Column(db.String(150))                                 #주소
    sacontact = db.Column(db.String(50))                               #연락처
    saemail = db.Column(db.String(50))                                 #회사 담당자 이메일(대표이메일)
    sadate = db.Column(db.String(50))                                  #등록한 날짜
    osworking_hours = db.relationship('OSWorking_hour')                #외래키 연동

class OSWorking_hour(db.Model):                                        #외주근무시간 저장
    id = db.Column(db.Integer, primary_key=True)                       #DB primary_key ID
    pcode = db.Column(db.String(50))                                   #프로젝트 코드(Order No)
    saname = db.Column(db.String(100))                                 #회사명()
    part = db.Column(db.String(50))                                    #외주 분야
    workhour = db.Column(db.Integer)                                   #근무 시간
    date = db.Column(db.DateTime(timezone=True), default=func.now())   #timestamp
    cocompanys = db.Column(db.Integer,db.ForeignKey('cocompany.id'))   #외래키 연동

