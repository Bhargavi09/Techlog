import re
from flask import *
import os
from datetime import date, datetime
from flaskext.mysql import MySQL
from pymysql import NULL, connect
from pymysql.cursors import Cursor


mysql=MySQL()

app=Flask(__name__)

app.secret_key = "bhargavi09"
app.config['MYSQL_DATABASE_USER']='root'
app.config['MYSQL_DATABASE_PASSWORD']=''
app.config['MYSQL_DATABASE_HOST']='localhost'
app.config['MYSQL_DATABASE_DB']='blogsite'

mysql.init_app(app)

@app.route('/admin')
def base():
    if 'loggedin' in session:
        return render_template('admin.html', username =session['username']) 
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    mycon = mysql.connect()
    mycur = mycon.cursor()
    msg=''
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        mycur.execute("SELECT * from user WHERE username = %s AND password=%s", (username,password))
        record = mycur.fetchone()
        if record:
            session['loggedin'] = True
            session['username'] = record[1]
            return redirect(url_for('base'))
        else:
            msg="Incorrect username/passowrd. Try again"
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('login'))



@app.route('/', defaults={'page':1})
@app.route('/page/<int:page>')
def home(page):
    perPage = 5
    startAt = page*perPage - perPage
    mycon = mysql.connect()
    mycur = mycon.cursor()
    mycur.execute("select * from blogpost where status='livepost' limit %s, %s;", (startAt, perPage))
    data = mycur.fetchall()
    mycur.execute("select * from blogpost order by dateandtime desc limit 5")
    recent = mycur.fetchall()
    print(recent)
    count = mycur.fetchone()
    return render_template('blog.html', data=data, recent=recent, count=count)





@app.route('/blogsingle/<id>')
def blogpost(id):
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("select * from blogpost where uid=%s",id)
    data=mycur.fetchall()
    mycur.execute("select * from blogpost order by dateandtime desc")
    recent = mycur.fetchall()
    mycur.execute("select * from feedback where post_id=%s",id)
    comments=mycur.fetchall()
    mycur.execute("select count(*) from feedback where post_id=%s",id)
    count = mycur.fetchone()
    return render_template('blog-single.html', data=data, recent=recent,comments=comments, count=count ) 

# @app.route('/blogpost')
# def blogpost():
#     return render_template('blog-single.html') 



@app.route('/insertRecord',methods=['POST'])
def insertrecord():
    photo=request.files['photo']
    authorphoto = request.files['authorphoto']
    mycon=mysql.connect()
    mycur=mycon.cursor()
    today=date.today()
    fromdate=today.strftime("%Y-%m-%d")
    status='livepost'
    data=[request.form['postname'],request.form['posttitle'],photo.filename,request.form['introduction'],request.form['postcontent'],request.form['conclusion'],fromdate,status, request.form['authorname'], request.form['authorbio'],authorphoto.filename]
    res = mycur.execute("INSERT INTO `blogpost`(`postname`, `posttitle`,`postimage`,`introduction`,`postcontent`,`conclusion`,`dateandtime`,`status`,`authorname`, `authorbio`,`authorphoto`) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",data)
    photo.save(os.path.join('static/upload',photo.filename))
    authorphoto.save(os.path.join('static/upload',authorphoto.filename))
    
    mycon.commit()
    return redirect(url_for('managepost'))

@app.route('/updateRecord/<id>',methods=['POST'])
def updaterecord(id):
    mycon=mysql.connect()
    mycur=mycon.cursor()
    today=date.today()
    fromdate=today.strftime("%Y-%m-%d")
    status='livepost'
    photo=request.files['photo']
    data=[request.form['postname'],request.form['posttitle'],photo.filename,request.form['postcontent'],fromdate,status,id]
    if photo:
        photo.save(os.path.join('static/upload',photo.filename))
        mycur.execute("UPDATE blogpost set postname=%s, posttitle=%s, postimage=%s,postcontent=%s,dateandtime=%s, status=%s where uid=%s",data)
    else:
        mycur.execute("SELECT postimage from blogpost WHERE uid=%s", id)
        fileName = mycur.fetchall()[0][0]
        data=[request.form['postname'],request.form['posttitle'],fileName,request.form['postcontent'],fromdate,status,id]
        mycur.execute("UPDATE blogpost set postname=%s, posttitle=%s, postimage=%s,postcontent=%s,dateandtime=%s, status=%s where uid=%s",data)
    mycon.commit()
    return redirect(url_for('managepost'))
    
@app.route('/managepost',methods=['GET'])
def managepost():
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("select * from blogpost where status='livepost'")
    data=mycur.fetchall()
    return render_template('managepost.html',data=data)
  
@app.route('/deletepost',methods=['GET'])
def deletepost():
    uid=request.args.get('uid')
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("update blogpost set status='deleted' where uid=%s",uid)
    mycon.commit()
    return redirect(url_for('managepost'))

@app.route('/editpost',methods=['GET'])
def editpost():
    uid=request.args.get('uid')
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("select * from blogpost where uid=%s",uid)
    data=mycur.fetchall()
    return render_template('editpost.html', data=data)

@app.route('/removedpost',methods=['GET'])
def removedpost():
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("select * from blogpost where status='deleted'")
    data=mycur.fetchall()
    return render_template('deletedpost.html',data=data)

@app.route('/restorepost',methods=['GET'])
def restorepost():
    uid=request.args.get('uid')
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("update blogpost set status='livepost' where uid=%s",uid)
    mycon.commit()
    return redirect(url_for('managepost'))

@app.route('/category/<cat>', methods=['GET'])
def category(cat):
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("SELECT * from blogpost WHERE postname=%s", cat)
    data = mycur.fetchall()
    mycur.execute("select * from blogpost order by dateandtime desc")
    recent = mycur.fetchall()
    mycur.execute("SELECT count(*) from blogpost WHERE postname=%s", cat)
    count = mycur.fetchone()
    return render_template('blog.html', data=data, recent=recent, count=count)

@app.route('/reply',methods=['POST'])
def reply():
    mycon=mysql.connect()
    mycur=mycon.cursor()
    post_id=request.form['post_id']
    data=[request.form['post_id'], request.form['name'],request.form['email'],request.form['comment'],datetime.now().strftime("%Y%m%d%H%M%S")]
    mycur.execute("INSERT INTO `feedback`(`post_id`, `name`, `email`,`comment`, `date`) VALUES(%s,%s,%s,%s,%s)",data)
    mycon.commit()
    return redirect(url_for('blogpost', id=post_id))

@app.route('/about')
def about():
    mycon=mysql.connect()
    mycur=mycon.cursor()
    mycur.execute("select * from blogpost")
    res = mycur.fetchall()
    return render_template('home.html', res=res)
   




app.run(debug=True,port=565323)    