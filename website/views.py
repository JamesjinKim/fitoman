from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Project, Cocompany,Working_hour, User
from . import db
from sqlalchemy import func, desc,  cast, Integer, literal_column, text
import json
from datetime import date, timedelta ,datetime
import holidays
import pandas as pd

views = Blueprint('views', __name__)

# 대한민국 공휴일 생성
kr_holidays = holidays.KR()

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
    try:
        # 업무 리스트 데이터 생성
        task_list = {
            "설계": ["설계", "현장지원", "SETUP"],
            "전장": ["전장설계", "전장조립", "SETUP"],
            "제어": ["PC제어", "PLC제어","비젼개발", "SETUP"],
            "기술": ["조립", "현장관리", "SETUP"]
            }
            
        if request.method == 'POST': 
            pcode = request.form.get('pcode')
            pname = request.form.get('pname')
            uname = request.form.get('username')
            jobpart = request.form.get('jobpart')
            workhour = request.form.get('workhour')
            recodingdate = request.form.get('recodingdate')
            
            # 필수 필드 검증
            if not all([pcode, pname, uname, jobpart, workhour]):
                flash("모든 필수 항목을 입력해주세요.", category='error')
                return redirect(url_for('views.work_hour'))
            
            # 작업시간 유효성 검사
            try:
                workhour = float(workhour)
                if workhour <= 0 or workhour > 24:
                    flash("유효한 작업시간을 입력해주세요 (0-24시간).", category='error')
                    return redirect(url_for('views.work_hour'))
            except ValueError:
                flash("작업시간은 숫자로 입력해주세요.", category='error')
                return redirect(url_for('views.work_hour'))

            if recodingdate == "":
                recodingdate = date.today()
            
            try:
                workhours = Working_hour(pcode=pcode,pname=pname,username=uname,
                                     jobpart=jobpart,workhour=workhour,recodingdate=recodingdate, user_id=current_user.id )
                db.session.add(workhours)
                db.session.commit()
                msg = "데이터 저장이 완료되었습니다."
                flash(msg, category='success')
            except Exception as e:
                db.session.rollback()
                flash("데이터 저장 중 오류가 발생했습니다.", category='error')
                return redirect(url_for('views.work_hour'))
        
        # 오늘, 어제 날짜 계산
        today = date.today()
        yesterday = today - timedelta(days=1)
        one_month_ago = today - timedelta(days=30)

        # 주말 또는 공휴일 여부 확인
        if is_weekend_or_holiday(yesterday):
            flash("어제는 주말 또는 공휴일이므로 근무 시간을 입력하지 않습니다.", category='info')

        else:  # 주말이 아닌 경우에만 어제 데이터 확인
            try:
                # 어제 날짜의 데이터가 있는지 확인
                yesterday_data = Working_hour.query.filter(
                    Working_hour.recodingdate == yesterday,
                    Working_hour.user_id == current_user.id
                ).first()
                if not yesterday_data:
                    flash("어제의 근무시간 기록이 입력되지 않았습니다.", category='error')
            except Exception as e:
                flash("데이터 조회 중 오류가 발생했습니다.", category='error')

        try:
            # 종료되지 않은 프로젝트 리스트
            projects = Project.query.with_entities(Project.pcode, Project.pname).filter(Project.enddate > today).all()

            # 한 달 전부터 오늘까지의 근무 시간 데이터 가져오기
            wh_data = Working_hour.query.filter(
                Working_hour.recodingdate >= one_month_ago,
                Working_hour.user_id == current_user.id
            ).order_by(Working_hour.recodingdate.desc()).all()

            return render_template("work_hour.html", data=task_list, all_data=projects, wh_data=wh_data, user=current_user)
        except Exception as e:
            flash("프로젝트 데이터 조회 중 오류가 발생했습니다.", category='error')
            return render_template("work_hour.html", data=task_list, all_data=[], wh_data=[], user=current_user)
            
    except Exception as e:
        flash(f"작업시간 입력 중 오류가 발생했습니다: {str(e)}", category='error')
        return render_template("work_hour.html", data=task_list, all_data=[], wh_data=[], user=current_user)

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
        flash("정보가 잘 저장되었습니다.")
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
        try:
            pcode = request.form.get('projCode')
            pname = request.form.get('projName')
            pdesc = request.form.get('pdesc')
            startdate = request.form.get('startDate')
            enddate = request.form.get('endDate')
            
            # 필수 필드 검증
            if not all([pcode, pname, startdate, enddate]):
                flash("모든 필수 항목을 입력해주세요.", category='error')
                return redirect(url_for('views.project_create'))
            
            # 날짜 형식 검증
            try:
                datetime.strptime(startdate, '%Y-%m-%d')
                datetime.strptime(enddate, '%Y-%m-%d')
            except ValueError:
                flash("올바른 날짜 형식이 아닙니다.", category='error')
                return redirect(url_for('views.project_create'))

            proj = Project(pcode=pcode, pname=pname, pdesc=pdesc,
                         startdate=startdate, enddate=enddate,
                         user_id=current_user.id)
            db.session.add(proj)
            db.session.commit()
            flash("정보가 잘 저장되었습니다.", category='success')
            
        except Exception as e:
            db.session.rollback()
            flash(f"프로젝트 생성 중 오류가 발생했습니다: {str(e)}", category='error')

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
        flash("정보가 잘 변경 되었습니다.")
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
        saemail = request.form.get('saemail')
        today = date.today().strftime("%Y-%m-%d")
        cocomp = Cocompany(saname=saname,sourcingjob=sourcingjob,
                       saboss=saboss,saaddr=saaddr,sacontact=sacontact,saemail=saemail,sadate=today)
        db.session.add(cocomp)
        db.session.commit()
        msg = "정보가 잘 저장되었습니다."
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
        ).order_by(
        Working_hour.recodingdate.desc()
        ).all()
    # pcode로 그룹핑하여 workhour 합산
    all_data_by_pcode = db.session.query(
        Working_hour.pcode,
        Working_hour.pname,
        Working_hour.username,
        Working_hour.jobpart,
        func.sum(Working_hour.workhour).label('workhour'),
        Working_hour.recodingdate
    ).group_by(
        Working_hour.pcode,
        Working_hour.pname,
        Working_hour.username,
        Working_hour.jobpart,
        Working_hour.recodingdate
    ).order_by(
        Working_hour.pcode.asc(),
        Working_hour.recodingdate.asc() #desc()
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

    return render_template("workhourtotal.html",all_data=all_data,user=current_user)

#일일현황 - 날짜별 부서별 jobpart별 업무시간
@views.route('/getdata_bydate', methods=['GET', 'POST'])
@login_required
def getdata_bydate():
    #프로젝트 목록 가져와 선택옵션으로 주기
    all_project = all_projects()
    if request.method == 'POST': 
        pcode = request.form.get('pcode',default="all")
        print(pcode)
        # 함수 호출 및 사용
        results = get_data_by_department_jobpart(pcode)
        print(results)

        
    else:
        
        return render_template('data_by.html',all_project=all_project,user=current_user)
    # Step 4: 데이터를 HTML 템플릿으로 전달
    return render_template('data_by.html',all_project=all_project,data=results, user=current_user)

@views.route('/get_user_summary', methods=['GET','POST'])
@login_required 
def get_user_summary(): 
    user_name = request.form.get('iuname',default="")
    from_date = request.form.get('from_date',default=date.today())
    to_date = request.form.get('to_date',default=date.today())
    if user_name != "All":
        working_hours = db.session.query(
            Working_hour.username,
            Working_hour.pcode,
            Working_hour.pname,
            User.udepartment,
            Working_hour.jobpart,
            Working_hour.recodingdate,
            func.sum(Working_hour.workhour).label('total_workhour')
        ).join(
                User, Working_hour.user_id == User.id
        ).filter(
            Working_hour.username == user_name,
            Working_hour.recodingdate >= from_date,
            Working_hour.recodingdate <= to_date
        ).group_by(
            Working_hour.username,
            Working_hour.pcode,
            Working_hour.pname,
            User.udepartment,
            Working_hour.jobpart,
            Working_hour.recodingdate
        ).order_by(
            Working_hour.recodingdate.asc(),
            Working_hour.pcode.asc()
        ).all()
        print(user_name)
        print(working_hours) 
        usersnames = get_username()
        return render_template('user_summary.html',uname=user_name, from_date=from_date, to_date=to_date,
                           working_hours=working_hours,users_name=usersnames, user=current_user)
    else:
        working_hours = db.session.query(
            Working_hour.username,
            Working_hour.pcode,
            Working_hour.pname,
            User.udepartment,
            Working_hour.jobpart,
            Working_hour.recodingdate,
            func.sum(Working_hour.workhour).label('total_workhour')
        ).join(
            User, Working_hour.user_id == User.id  # join 추가
        ).filter(
            Working_hour.recodingdate >= from_date,
            Working_hour.recodingdate <= to_date
        ).group_by(
            Working_hour.username,
            Working_hour.pcode,
            Working_hour.pname,
            User.udepartment,
            Working_hour.jobpart,
            Working_hour.recodingdate
        ).order_by(
            Working_hour.recodingdate.asc(),
            Working_hour.pcode.asc()
        ).all()
        print(user_name)
        usersnames = get_username()
        return render_template('user_summary.html',uname=user_name, from_date=from_date, to_date=to_date,
                           working_hours=working_hours,users_name=usersnames, user=current_user)


def all_projects():
    #종료일이 오늘 이후 것 가져옴
    today = date.today()
    # 모든 프로젝트 가져오기
    projects = db.session.query(Project).all()

    # 필터링: enddate가 오늘 이후인 프로젝트만 선택
    all_projects = [
    project for project in projects
    if datetime.strptime(project.enddate, '%Y-%m-%d').date() >= today]
    return all_projects

def is_weekend_or_holiday(check_date):
    # 주말인지 확인 (토요일: 5, 일요일: 6)
    if check_date.weekday() in [5, 6]:
        return True
    # 공휴일인지 확인
    if check_date in kr_holidays:
        return True
    return False

def get_data_by_department_jobpart(pcode):
    today = date.today()
    try:
        if not isinstance(pcode, str):
            raise ValueError("프로젝트 코드는 문자열이어야 합니다.")
            
        query = db.session.query(
            Working_hour.pcode,
            User.udepartment, 
            Working_hour.jobpart,
            cast(func.sum(Working_hour.workhour), Integer).label('total_hours')
        ).join(User, User.id == Working_hour.user_id)
        
        if pcode == "all":
            query = query.join(Project, Project.pcode == Working_hour.pcode)\
                        .filter(func.date(Project.enddate) < today)
        else:
            query = query.filter(Working_hour.pcode == pcode)
            
        result = query.group_by(
            Working_hour.pcode, User.udepartment, Working_hour.jobpart
        ).order_by(
            Working_hour.pcode, User.udepartment, Working_hour.jobpart
        ).all()
        
        if not result:
            print("데이터가 없습니다.")
            return []
            
        return result
        
    except Exception as e:
        print(f"데이터 조회 중 오류 발생: {str(e)}")
        # 로깅 추가 권장
        return []

def get_data_by_date_department_jobpart(pcode):
    try:
        if pcode == "all":
            data_by_date_department_jobpart = db.session.query(
                Working_hour.recodingdate,
                User.udepartment, 
                Working_hour.jobpart,
                cast(func.sum(Working_hour.workhour), Integer).label('total_hours')
                ).join(Working_hour, User.id == Working_hour.user_id
                ).group_by(User.udepartment, Working_hour.recodingdate, Working_hour.jobpart,
                ).order_by(db.func.row_number().over(partition_by=User.udepartment, order_by=Working_hour.recodingdate.desc())
                ).all()
            
                   #.order_by(Working_hour.recodingdate.desc()).all()
        else :
            data_by_date_department_jobpart = db.session.query(
                Working_hour.recodingdate,
                User.udepartment, 
                Working_hour.jobpart,
                cast(func.sum(Working_hour.workhour), Integer).label('total_hours')
                ).join(Working_hour, User.id == Working_hour.user_id  # Project 테이블과 JOIN
                ).filter(Working_hour.pcode == pcode  # pcode 조건 추가
                ).group_by(User.udepartment, Working_hour.recodingdate, Working_hour.jobpart
                ).order_by(Working_hour.recodingdate.desc()).all()
        if not data_by_date_department_jobpart:
            print("데이터가 없습니다.")
        
        return data_by_date_department_jobpart

    except Exception as e:
        print("An error occurred:", e)
        return []
    

def get_username():
    try:
        get_usersname = db.session.query(
            User.uname    
        ).all()

        if not get_usersname:
            print("No data found")
        
        return get_usersname

    except Exception as e:
        print("An error occurred:", e)
        return []




