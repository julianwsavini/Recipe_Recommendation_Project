from flask import Flask, Blueprint, render_template, request


app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        first_nam = request.form.get("fname")
        last_nam = request.form.get("lname")
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True, port=8000)