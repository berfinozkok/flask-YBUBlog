from flask import Flask, render_template


app= Flask(__name__)
@app.route("/")
def index():
    article=dict()
    article["title"]= "Deneme"
    article["body"]= "Deneme 123"
    article["author"]="Berfin"
    return render_template("index.html", article=article)

@app.route("/about")
def about():
    return "About me"

if __name__ =="__main__": 
    app.run(debug=True)