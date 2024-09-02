from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Project, Cocompany,Working_hour, User
from . import db
from sqlalchemy import func, desc
import json
from datetime import date, timedelta ,datetime

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
        
    all_data = Note.query.order_by(desc(Note.date)).all()

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
        recodingdate = request.form.get('recodingdate')
        if recodingdate == "":
            recodingdate = date.today()
        workhours = Working_hour(pcode=pcode,pname=pname,username=uname,
                                 jobpart=jobpart,workhour=workhour,recodingdate=recodingdate, user_id=current_user.id )
        db.session.add(workhours)
        db.session.commit()
        msg = "Record successfully added to database"
        flash(msg, category='success')
    
     # 오늘, 어제 날짜 계산
    today = date.today()
    yesterday = today - timedelta(days=1)
    one_month_ago = today - timedelta(days=30)

    # 어제 날짜의 데이터가 있는지 확인
    yesterday_data = Working_hour.query.filter(
        Working_hour.recodingdate == yesterday,
        Working_hour.user_id == current_user.id
    ).first()

    if not yesterday_data:
        flash("No Data for yesterday", category='error')
    else:
        flash("Data for yesterday exists", category='success')

    # 종료되지 않은 프로젝트 리스트
    projects = Project.query.with_entities(Project.pcode, Project.pname).filter(Project.enddate > today).all()

    # 한 달 전부터 오늘까지의 근무 시간 데이터 가져오기
    wh_data = Working_hour.query.filter(
        Working_hour.recodingdate >= one_month_ago,
        Working_hour.user_id == current_user.id
    ).order_by(Working_hour.recodingdate.desc()).all()

    return render_template("work_hour.html", task_list=task_list, all_data=projects, wh_data=wh_data, user=current_user)

@views.route('/workhour_update', methods = ['POST'])
def workhour_update():
    if request.method == "POST":
        my_data = Working_hour.query.get(request.form.get('id'))
        my_data.pcode = request.form.get('pcode')
        my_data.pname = request.form.get('pname')
        my_data.username = request.form.get('username')
        my_data.jobpart = request.form.get('jobpart')
        my_data.workhour = request.form.get('workhour')
        recodedate = request.form.get('recodingdate')
        if recodedate != "":
            my_data.recodingdate = recodedate
        
        db.session.commit()
        flash("Employee Updated Successfully")
        return redirect(url_for('views.work_hour'))

@views.route('/workhour_delete/<id>', methods=['GET','POST'])
@login_required
def workhour_delete(id):  
    workhour = Working_hour.query.get(id)
    if workhour:
        db.session.delete(workhour)
        db.session.commit()
        flash('업무 시간이 삭제되었습니다.')
    return redirect(url_for('views.work_hour'))

@views.route('/project_view', methods=['GET', 'POST'])
@login_required
def project_view():
    # 업무 리스트 데이터 생성
    task_list = ["전장외주","조립외주","제어외주","기타"]
    
    all_data = all_projects()
    return render_template("projectview.html",task_list=task_list, all_data=all_data, user=current_user)

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

    all_data = all_projects()
    return render_template("projectcreate.html",all_data=all_data, user=current_user)

@views.route('/project_update', methods=['GET','POST'])
@login_required
def project_update():
    if request.method == "POST":
        my_data = Project.query.get(request.form.get('pid'))
        my_data.pcode = request.form.get('pcode')
        my_data.pname = request.form.get('pname')
        my_data.pdesc = request.form.get('pdesc')
        startdate = request.form.get('startDate')
        enddate = request.form.get('endDate')
        if startdate != '' and enddate != '':
            my_data.startdate = request.form.get('startDate')
            my_data.enddate = request.form.get('endDate')
        
        print(my_data)
        db.session.commit()
        flash("Project Updated Successfully")
        return redirect(url_for('views.project_create'))

@views.route('/project_delete/<pid>/', methods=['GET', 'POST'])
@login_required
def project_delete(pid):  
    my_data = Project.query.get(pid)    
    if my_data:
        if my_data.user_id == current_user.id:
            db.session.delete(my_data)
            db.session.commit()
            flash("Project 삭제가 완료되었습니다.")
        else:
            flash("Project를 생성한 사람만 삭제 가능합니다.",category='error')

    return redirect(url_for('views.project_create'))

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
        cocomp = Cocompany(saname=saname,sourcingjob=sourcingjob,
                       saboss=saboss,saaddr=saaddr,sacontact=sacontact,sadate=today)
        db.session.add(cocomp)
        db.session.commit()
        msg = "Record successfully added to database"
        flash(msg, category='success')
        
    task_list = ["전장외주","조립외주","제어외주","기타"]    
    all_data = Cocompany.query.all()
    return render_template("cocompanycreate.html", task_list=task_list, all_data=all_data, user=current_user)

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
    all_data = db.session.query(
            Working_hour.pcode,
            Working_hour.pname,
            Working_hour.username,
            Working_hour.jobpart,
            Working_hour.workhour,
            Working_hour.recodingdate
            ).all()
    # pcode로 그룹핑하여 workhour 합산
    all_data_by_pcode = db.session.query(
        Working_hour.pcode,
        Working_hour.pname,
        Working_hour.jobpart,
        func.sum(Working_hour.workhour).label('workhour'),
        Working_hour.recodingdate
    ).group_by(
        Working_hour.pcode,
        Working_hour.pname,
        Working_hour.jobpart,
        Working_hour.recodingdate
    ).order_by(
        Working_hour.pcode.asc(),
        Working_hour.recodingdate.asc()
    ).all()
    #username으로 그룹핑하여 workhour 합산
    all_data_by_username = db.session.query(
        Working_hour.username,
        func.sum(Working_hour.workhour).label('workhour')
    ).group_by(Working_hour.username).all()
    #recodingdate로 그룹핑하여 workhour 합산
    all_data_by_recodingdate = db.session.query(
        Working_hour.recodingdate,
        func.sum(Working_hour.workhour).label('workhour')
    ).group_by(Working_hour.recodingdate).all()
    #recodingdate를 from-to 조건으로 필터링하여 데이터 조회
    # start_date = datetime.strptime('2024-08-01', '%Y-%m-%d').date()
    # end_date = datetime.strptime('2024-09-31', '%Y-%m-%d').date()

    # all_data_by_date_range = db.session.query(
    #     Working_hour.pcode,
    #     Working_hour.pname,
    #     Working_hour.username,
    #     Working_hour.jobpart,
    #     Working_hour.workhour,
    #     Working_hour.recodingdate
    # ).filter(
    #     Working_hour.recodingdate.between(start_date, end_date)
    # ).all()
    #pcode와 recodingdate로 동시에 그룹핑하여 workhour 합산
    all_data_by_pcode_and_date = db.session.query(
            Working_hour.pcode,
            Working_hour.recodingdate,
            func.sum(Working_hour.workhour).label('workhour')
        ).group_by(
            Working_hour.pcode,
            Working_hour.recodingdate
        ).order_by(
            Working_hour.pcode.asc(),
            Working_hour.recodingdate.asc()
        ).all()

    return render_template("workhourtotal.html",all_data=all_data_by_pcode,user=current_user)

@views.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    if request.method == 'POST': 
        pcode = request.form.get('pcode')
        pname = request.form.get('pname')
        startDate = request.form.get('startDate').replace('-', ', ')
        endDate = request.form.get('endDate').replace('-', ', ')
        #recodingdate를 from-to 조건으로 필터링하여 데이터 조회
        start_date = datetime.strptime('2024-08-01', '%Y-%m-%d').date()
        end_date = datetime.strptime('2024-09-31', '%Y-%m-%d').date()

        all_data_by_date_range = db.session.query(
            Working_hour.pcode,
            Working_hour.pname,
            Working_hour.username,
            Working_hour.jobpart,
            Working_hour.workhour,
            Working_hour.recodingdate
        ).filter(
            Working_hour.recodingdate.between(start_date, end_date)
        ).all()

        # User 테이블을 조인하여 pcode와 jobpart별로 그룹핑하고 workhour를 합산
        all_data_by_pcode_jobpart_department = db.session.query(
            Working_hour.pcode,
            User.udepartment,
            Working_hour.jobpart,
            func.sum(Working_hour.workhour).label('workhours')
        ).join(
            User, Working_hour.user_id == User.id  # User 테이블과 조인
        ).group_by(
            Working_hour.pcode,
            User.udepartment,
            Working_hour.jobpart
        ).order_by(
            Working_hour.pcode.asc(),
            User.udepartment.asc(),
            Working_hour.jobpart.asc()
        ).all()
        # 조건절을 추가한 Query  .filter()
        all_data_by_pcode = db.session.query(
            Working_hour.pcode,
            Working_hour.pname,
            Working_hour.jobpart,
            func.sum(Working_hour.workhour).label('total_workhours'),
            Working_hour.recodingdate
        ).filter(
            Working_hour.pcode == '0777'  # 특정 pcode 조건 추가
        ).group_by(
            Working_hour.pcode,
            Working_hour.pname,
            Working_hour.jobpart,
            Working_hour.recodingdate
        ).order_by(
            Working_hour.pcode.asc(),
            Working_hour.recodingdate.asc()
        ).all()
    return render_template('test1.html', user=current_user)

@views.route('/work_hours_summary', methods=['GET', 'POST'])
@login_required
def work_hours_summary():
    # 데이터베이스에서 쿼리 수행
    all_data_by_pcode_jobpart_department = db.session.query(
        Working_hour.pcode,
        Working_hour.jobpart,
        User.udepartment,
        func.sum(Working_hour.workhour).label('total_workhours')
    ).filter(
        Working_hour.pcode == '0777'  # 특정 pcode 조건 추가
    ).join(
        User, Working_hour.user_id == User.id
    ).group_by(
        Working_hour.pcode,
        Working_hour.jobpart,
        User.udepartment
    ).order_by(
        Working_hour.pcode.asc(),
        Working_hour.jobpart.asc(),
        User.udepartment.asc()
    ).all()

    # HTML 템플릿으로 데이터 전달
    return render_template('work_hours_summary.html', data=all_data_by_pcode_jobpart_department, user=current_user)

def all_projects():
     #종료일이 오늘 이후 것 가져옴
    today = date.today()
    all_projects = db.session.query(
        Project.pid,
        Project.pcode,
        Project.pname,
        Project.startdate,
        Project.enddate,
        Project.pdesc,
    func.strftime('%y-%m-%d', Project.date).label('date')).filter(Project.enddate >= today).all()
    return all_projects
