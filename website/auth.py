from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    # 리스트 데이터 생성
    task_list = ["영업","설계","전장","기술","제어","외주"]
    if request.method == 'POST':
        email = request.form.get('email')
        uname = request.form.get('userName')
        uDepart = request.form.get('uDepartment')
        uPosition = request.form.get('uPosition')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        authority = '1'  #임시 하드코딩 저장... 1,2,3(1 슈퍼 관리자, 2 관리자, 3 일반 사용자)

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif email.find('@') == -1: #len(email) < 4:
            flash('Email must be @ characters.', category='error')
        elif len(uname) < 3:
            flash('User name must be greater than 2 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 5:
            flash('Password must be at least 5 characters.', category='error')
        else:
            new_user = User(email=email, uname=uname,udepartment=uDepart,uposition=uPosition, 
                            password=generate_password_hash(password1, method='pbkdf2:sha256'),
                            authority=authority
                            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", task_list=task_list, user=current_user)

@auth.route('/userinfo_update', methods=['GET', 'POST'])
def userinfo_update():
    if request.method == 'POST':
        my_data = User.query.get(request.form.get('id'))
        my_data.email = request.form.get('email')
        my_data.uname = request.form.get('uname')
        my_data.udepartment = request.form.get('udepartment')
        my_data.uposition = request.form.get('uposition')
        my_data.authority = request.form.get('authority')
        db.session.commit()
        flash("UserInfo Updated Successfully")
    all_data = User.query.all()
    return render_template("user_info.html", all_data=all_data, user=current_user)

@auth.route('/userdelete/<id>/', methods=['GET', 'POST'])
def userdelete(id):
    if request.method == 'POST':
        my_data = User.query.get(id)
        db.session.delete(my_data)
        db.session.commit()
        flash("User Deleted Successfully")
    all_data = User.query.all()
    return render_template("user_info.html", all_data=all_data, user=current_user)
