from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "segredo_super_secreto"

# banco
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 👤 usuário
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# 📌 tarefa
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    deadline = db.Column(db.DateTime)

# 🔥 recriar banco (use só se precisar corrigir erro)
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
    return render_template('index.html', tasks=tasks, now=datetime.now())

# ➕ adicionar tarefa
@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    deadline = request.form.get('deadline')

    task = Task(
        title=request.form['title'],
        user_id=session['user_id'],
        deadline=datetime.strptime(deadline, "%Y-%m-%d") if deadline else None
    )

    db.session.add(task)
    db.session.commit()
    return redirect('/')

# ✔ concluir tarefa
@app.route('/done/<int:id>')
def done(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get(id)

    # 🔒 garante que a tarefa é do usuário logado
    if task and task.user_id == session['user_id']:
        task.done = not task.done
        db.session.commit()

    return redirect('/')

# ❌ deletar tarefa
@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get(id)

    # 🔒 segurança
    if task and task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()

    return redirect('/')

# ✏️ editar tarefa
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Task.query.get(id)

    # 🔒 segurança
    if not task or task.user_id != session['user_id']:
        return redirect('/')

    if request.method == 'POST':
        task.title = request.form['title']

        deadline = request.form.get('deadline')
        task.deadline = datetime.strptime(deadline, "%Y-%m-%d") if deadline else None

        db.session.commit()
        return redirect('/')

    return render_template('edit.html', task=task)

if __name__ == '__main__':
    app.run(debug=True)