from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Project, Cocompany,Working_hour
from . import db
from sqlalchemy import func
import json
from datetime import date

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')#Gets the note from the HTML 

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            name = current_user.uname
            new_note = Note(data=note, noteuname=name, user_id=current_user.id)  #providing the schema for the note 
            db.session.add(new_note) #adding the note to the database 
            db.session.commit()
            flash('Note added!', category='success')
        
    all_data = Note.query.all()

    return render_template("home.html", all_data=all_data, user=current_user)


@views.route('/delete_note', methods=['POST'])
@login_required
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

#workhour_modal
@views.route('/work_hour', methods=['GET','POST'])
@login_required
def work_hour():  
    # 업무 리스트 데이터 생성
    task_list = ["기구설계","현장지원","전장설계","조립",
                 "PC제어","PLC제어", "셋업", "기타"]
    if request.method == 'POST': 
        pcode = request.form.get('pcode')
        pname = request.form.get('pname')
        uname = request.form.get('username')
        jobpart = request.form.get('jobpart')
        workhour = request.form.get('workhour')
        workhours = Working_hour(pcode=pcode,pname=pname,username=uname,
                                 jobpart=jobpart,workhour=workhour,user_id=current_user.id )
        db.session.add(workhours)
        db.session.commit()
        msg = "Record successfully added to database"
        flash(msg, category='success')
    projects = Project.query.with_entities(Project.pcode,Project.pname).all()
    print(projects)
    wh_data=Working_hour.query.all()
    return render_template("work_hour.html", task_list=task_list, all_data=projects,wh_data=wh_data, user=current_user)

@views.route('/workhour_update', methods = ['POST'])
def workhour_update():
    if request.method == "POST":
        my_data = Working_hour.query.get(request.form.get('id'))
        my_data.pcode = request.form.get('pcode')
        my_data.pname = request.form.get('pname')
        my_data.username = request.form.get('username')
        my_data.jobpart = request.form.get('jobpart')
        my_data.workhour = request.form.get('workhour')
        db.session.commit()
        flash("Employee Updated Successfully")
        return redirect(url_for('views.work_hour'))

@views.route('/workhour_delete/<id>/')
@login_required
def workhour_delete(id): 
    my_data = Working_hour.query.get(id)
    db.session.delete(my_data)
    db.session.commit()

    flash("Data Deleted Successfully")
    return redirect(url_for('views.work_hour'))
    
@views.route('/project_create', methods=['GET', 'POST'])
@login_required
def project_create():
    if request.method == 'POST': 
        pcode = request.form.get('projCode')                                        #프로젝트코드
        pname = request.form.get('projName')                                        #프로젝트명
        pdesc = request.form.get('pdesc')                                           #프로젝트 설명
        startdate = request.form.get('startDate')                                   #시작일
        enddate = request.form.get('endDate')                                       #종료일

        proj = Project(pcode=pcode,pname=pname,pdesc=pdesc,startdate=startdate,enddate=enddate,
                       user_id=current_user.id )
        db.session.add(proj)
        db.session.commit()
        msg = "Record successfully added to database"
        flash(msg, category='success')
    all_data = Project.query.all()
    return render_template("projectcreate.html",all_data=all_data, user=current_user)

@views.route('/project_view', methods=['GET'])
@login_required
def project_view():

    all_data = Project.query.all()
    return render_template("projectview.html",all_data=all_data, user=current_user)

@views.route('/project_update', methods=['GET'])
@login_required
def project_update():

    if request.method == "POST":
        my_data = Working_hour.query.get(request.form.get('id'))
        my_data.pcode = request.form.get('pcode')
        my_data.username = request.form.get('username')
        my_data.part = request.form.get('part')
        my_data.workhour = request.form.get('workhour')
        db.session.commit()
        flash("Project Updated Successfully")
        return redirect(url_for('views.project_view'))


    all_data = Project.query.all()
    return render_template("projectview.html",all_data=all_data, user=current_user)


@views.route('/project_delete', methods=['POST'])
@login_required
def project_delete():  
    proj = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    pid = proj['pid']
    data = Project.query.get(pid)
    if data:
        if data.user_id == current_user.id:
            db.session.delete(data)
            db.session.commit()
    return jsonify({})

#Co Company Create
@views.route('/cocompany_create', methods=['GET', 'POST'])
@login_required
def cocompany_create():
    if request.method == 'POST': 
        saname = request.form.get('saname')
        sourcingjob = request.form.get('sourcingjob')
        saboss = request.form.get('saboss')
        saaddr = request.form.get('saaddr')
        sacontact = request.form.get('sacontact')
        today = date.today()
        sadate = today
        cocomp = Cocompany(saname=saname,sourcingjob=sourcingjob,
                       saboss=saboss,saaddr=saaddr,sacontact=sacontact,sadate=sadate)
        db.session.add(cocomp)
        db.session.commit()
        msg = "Record successfully added to database"
        flash(msg, category='success')
    else:
        all_data = Cocompany.query.all()
    return render_template("cocompanycreate.html", all_data=all_data, user=current_user)

@views.route('/cocompany_delete', methods=['POST'])
@login_required
def cocompany_delete():  
    proj = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    id = proj['id']
    data = Cocompany.query.get(id)
    if data:
        if data.user_id == current_user.id:
            db.session.delete(data)
            db.session.commit()
    return jsonify({})


@views.route('/workhour_total', methods=['GET', 'POST'])
@login_required
def workhour_total():
        # 시작 날짜와 종료 날짜 설정
        # from_day = '24-08-01'
        # to_day = '24-09-04'
        all_data = db.session.query(
                Working_hour.pcode,
                Working_hour.pname,
                Working_hour.username,
                Working_hour.jobpart,
                Working_hour.workhour,
                func.date(Working_hour.date).label('date')
                ).all()

        # all_data = db.session.query(
        #         Working_hour.pcode,
        #         Working_hour.pname,
        #         Working_hour.username,
        #         Working_hour.jobpart,
        #         func.sum(Working_hour.workhour).label('workhour'),
        #         func.date(Working_hour.date).label('date')
        #    ).group_by(Working_hour.pcode,func.date(Working_hour.date).label('date')).all()
        #all_data = Working_hour.query.all()
        return render_template("workhourtotal.html",all_data=all_data,user=current_user)

# 날짜 범위를 생성하는 함수
# def generate_date_range(start_date, end_date):
#     start = datetime.strptime(start_date, "%y-%m-%d")
#     end = datetime.strptime(end_date, "%y-%m-%d")
#     delta = timedelta(days=1)

#     date_list = []
#     current_date = start
#     while current_date <= end:
#         date_list.append(format_date(current_date))
#         current_date += delta

#     return date_list

# # 날짜 형식을 변환하는 함수
# def format_date(date):
#     weekdays = ["월", "화", "수", "목", "금", "토", "일"]
#     return date.strftime("%m월 %d일"({weekdays[date.weekday()]}))


@views.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    
    return render_template('test.html', user=current_user)

