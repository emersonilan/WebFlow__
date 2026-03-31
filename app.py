from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "segredo_super_secreto"

# banco
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 👤 tabela de usuários
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# 📌 tabela de tarefas
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# 🔥 CORREÇÃO DO ERRO (executar uma vez)
with app.app_context():
    db.create_all()

# 🔐 registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

# 🔑 login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            session['user_id'] = user.id
            return redirect('/')
        else:
            error = "Usuário ou senha incorretos"

    return render_template('login.html', error=error)

# 🚪 logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# 🏠 home
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    tasks = Task.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', tasks=tasks)

# ➕ adicionar tarefa
@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    task = Task(
        title=request.form['title'],
        user_id=session['user_id']
    )
    db.session.add(task)
    db.session.commit()
    return redirect('/')

# ✔ concluir
@app.route('/done/<int:id>')
def done(id):
    task = Task.query.get(id)
    if task:
        task.done = not task.done
        db.session.commit()
    return redirect('/')

# ❌ deletar
@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get(id)
    if task:
        db.session.delete(task)
        db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)