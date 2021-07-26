from flask import Flask, render_template, flash, redirect,url_for, session, logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField,validators #daha az kodla daha çok iş
from passlib.hash import sha256_crypt
from functools import wraps #for decorator
#User Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs) #çağırmak
        else:
            flash("To view this page, please sign in", "danger")
            return redirect(url_for("login"))
    return decorated_function

#User Register Form
class RegisterForm(Form):
    name= StringField("Name-Surname", validators= [validators.Length(min=4, max=25)])
    username= StringField("Username", validators= [validators.Length(min=5, max=35)])
    email= StringField("E-mail", validators= [validators.Email("Please enter a valid e-mail adress.")])
    password= PasswordField("Password:", validators=[validators.DataRequired(message= "Please enter a password"),
        validators.EqualTo(fieldname="confirm", message="Not correct Password!")
    ])
    confirm=PasswordField("Confirm Password")
class LoginForm(Form):
    username= StringField("Username:")
    password=PasswordField("Password:")

app= Flask(__name__)
app.secret_key="ybublog" #flash mesajlarını yayınlamak için secret key olmak zorunda
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ybublog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)
@app.route("/")
def index():
    articles =[
        {"id":1, "title": "First Article", "content": "First article components"},
        {"id":2, "title": "Second Article", "content": "Second article components"},
        {"id":3, "title": "Third Article", "content": "Third article components"}
    ]
    return render_template("index.html", articles=articles)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    query="Select * From articles"
    result=cursor.execute(query)

    if result > 0:
        articles=cursor.fetchall() #veritabanındaki makaleleri liste olarak görüntüleyecek
        return render_template("articles.html", articles=articles)

    else:
        return render_template("articles.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    query= "Select * from articles where author = %s"
    result=cursor.execute(query,(session["username"],))

    if result >0:
        articles=cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else: 
        return render_template("dashboard.html")


@app.route("/register", methods= ["GET", "POST"])
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and form.validate(): #indexe dönüş ve form check, T,F alır
        name=form.name.data #data bilgisini almak için
        username= form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data) #şifrelemek için
        cursor = mysql.connection.cursor() #phpmyadmin üzerinde gerekli cursor oluşturmak
        query= "Insert into users(name, email, username, password) VALUES(%s,%s,%s,%s)" #veritabanında tabloya ekleme
        cursor.execute(query,(name, email, username, password)) #execute çalıştırmak
        mysql.connection.commit() #veritabanında herhangi bir değişiklik varsa!!

        cursor.close() #arkadaki kaynakları gereksiz kullanmamak için
        flash("Succesfully registered.", "success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)
 
 #Login
@app.route("/login", methods= ["GET", "POST"])
def login():
    form=RegisterForm(request.form)
    if request.method =="POST":
        username= form.username.data
        password_entered=form.password.data
        cursor=mysql.connection.cursor()

        query= "Select * From users where username = %s"
        result= cursor.execute(query,(username,)) #if single use ","

        if result >0:
            data = cursor.fetchone()
            real_password= data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Successfully logged in", "success")
                session["logged_in"]=True
                session["username"]=username

                return redirect(url_for("index"))
            else:
                flash("Password not entered correctly", "danger")
                return redirect(url_for("login"))
        else:
            flash("Not registered user...", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)

#Detay
@app.route("/article/<string:id>")
def article(id):
    cursor= mysql.connection.cursor()
    query= "Select * from articles where id = %s"
    result= cursor.execute(query, (id,))
    if result>0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")


#Log out
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        cursor=mysql.connection.cursor()
        query="Insert into articles (title, author, content) VALUES(%s,%s,%s)"
        cursor.execute(query,(title, session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Article added successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form=form)
#Delete Article
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    query= "Select * from articles where author=%s and id=%s"
    result=cursor.execute(query,(session["username"],id))

    if result > 0:
        query2="Delete from articles where id = %s"
        cursor.execute(query2,(id,))

        mysql.connection.commit() #veritabanını değiştirmek için
        return redirect(url_for("dashboard"))

    else:
        flash("There is not such article or not commited action", "danger")
        return redirect(url_for("index"))

@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        query="Select * from articles where id = %s and author = %s"
        result=cursor.execute(query, (id, session["username"]))
        if result==0:
            flash("Not exceed", "danger")
            return redirect(url_for("index"))

        else:
            article=cursor.fetchone()
            form = ArticleForm()

            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("update.html", form=form)

    else:
        #POST REQUEST
        form=ArticleForm(request.form)
        newTitle= form.title.data
        newContent= form.title.data
        query2="Update articles Set title = %s, content = %s where id=%s"

        cursor=mysql.connection.cursor()
        cursor.execute(query2,(newTitle, newContent, id))
        mysql.connection.commit()
        flash("Article updated successfully..", "success")
        return redirect(url_for("dashboard"))


class ArticleForm(Form):
    title= StringField("Title of Article", validators= [validators.Length(min=5, max=100)])
    content= TextAreaField("Content of The Article", validators= [validators.Length(min=10)])

if __name__ =="__main__": 
    app.run(debug=True)